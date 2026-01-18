from fastapi import FastAPI, Depends, HTTPException, status
from typing import Optional
import os
from dotenv import load_dotenv
from pathlib import Path
from typing import List

from concurrent.futures import ThreadPoolExecutor
import peewee
from pydantic import BaseModel, Field

import asyncio

app = FastAPI()

# config.env 파일 경로를 명시적으로 지정
env_path = Path(__file__).parent / "config.env"

load_dotenv(dotenv_path=env_path)

DB_NAME = os.getenv("DB_NAME", "your_database_name")
PORT = os.getenv("PORT", "8000")

print("DB_NAME", DB_NAME)

db = peewee.SqliteDatabase(DB_NAME)

executor = ThreadPoolExecutor(max_workers=20) # 쓰레드 풀 생성 (동기 작업 처리용)

async def run_in_executor(func, *args, **kwargs):
    """동기 Peewee 작업을 별도의 쓰레드에서 실행하고 비동기로 결과를 기다립니다."""
    loop = asyncio.get_event_loop()
    return await loop.run_in_executor(executor, func, *args, **kwargs)

class BaseModelPeewee(peewee.Model):
    class Meta:
        database = db

# Peewee ORM 모델 정의
class ItemPeewee(BaseModelPeewee):
    name = peewee.CharField(index=True)
    price = peewee.FloatField()

# DB 및 테이블 초기화 함수
def create_tables():
    """테이블이 없으면 생성합니다."""
    with db:
        db.create_tables([ItemPeewee]) #if not exists


create_tables()
def db_operation(func, *args, **kwargs):
    """
    Peewee Context Manager를 사용하여 DB 연결을 열고,
    작업 완료 후 자동으로 닫는 동기 래퍼 함수입니다.
    """
    try:
        # with db: 블록이 db.connect()와 db.close()를 자동으로 처리합니다.
        with db:
            return func(*args, **kwargs)
    except Exception as e:
        # 트랜잭션 오류 처리 등 필요 시 여기에 추가
        raise e

# Pydantic 모델 정의
class ItemBase(BaseModel):
    name: str = Field(example="Peewee Book", min_length=3, max_length=50)
    price: float = Field(gt=0, example=35.00)

class ItemUpdate(BaseModel):
    name: Optional[str] = None
    price: Optional[float] = None

# 응답 모델 (Peewee 객체를 Pydantic으로 변환할 때 사용)
class Item(ItemBase):
    id: int = Field(example=1)

    # ORM 모드 설정: Peewee 객체를 Pydantic이 자동으로 읽을 수 있게 합니다.
    class Config:
        from_attributes = True # Pydantic v2


# Create (POST) {"name": "testuser", "price": 1.0}
@app.post("/items/", response_model=Item, status_code=status.HTTP_201_CREATED)
async def create_item(item: ItemBase):
    """
    새로운 아이템을 생성합니다.
    - 요청 본문은 ItemBase 모델을 따릅니다.
    """
    new_item = await run_in_executor(
            lambda: ItemPeewee.create(name=item.name, price=item.price)
        )
    return new_item

# Read All (PATCH)
@app.patch("/items/", response_model=List[Item])
async def read_items():
    """
    전체 아이템 목록을 조회합니다.
    실사용시에는 전체 목록을 제한적으로 조회하도록 합니다.
    너무 많은 데이터를 로드하다가 서버나 데이터베이스가 불안정해지기도 합니다.
    """
    items = await run_in_executor(lambda: list(ItemPeewee.select()))
    return items


# Read Single (GET)
@app.get("/items/{item_id}", response_model=Item)
async def read_item(item_id: int):
    # 순수한 CRUD 로직만 포함
    def get_item_by_id_pure(item_id: int):
        try:
            # 연결 및 닫기는 'db_operation'에서 처리하므로 생략
            return ItemPeewee.get_by_id(item_id)
        except ItemPeewee.DoesNotExist:
            return None

    # run_in_executor를 db_operation과 함께 사용
    db_item = await run_in_executor(db_operation, get_item_by_id_pure, item_id)

    if db_item is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Item not found")

    return db_item


# Update (PUT) - 부분 수정 (선택적 사용) {"name": "testuser", "price": 2.0}
@app.put("/items/{item_id}", response_model=Item)
async def partial_update_item(item_id: int, item_update: ItemUpdate):
    """
    특정 ID의 아이템 데이터만 수정합니다.
    """
    pass


# Delete (DELETE)
@app.delete("/items/{item_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_item(item_id: int):
    # 순수한 CRUD 로직만 포함
    def delete_item_pure(item_id: int):
        # delete() 쿼리를 실행하고 삭제된 행의 수를 반환
        rows_deleted = ItemPeewee.delete().where(ItemPeewee.id == item_id).execute()
        return rows_deleted

    rows_deleted = await run_in_executor(db_operation, delete_item_pure, item_id)

    if rows_deleted == 0:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Item not found")
    """
    특정 ID의 아이템 데이터를 삭제합니다.
    """
    pass