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

DB_NAME = "your_database_name"
db = peewee.SqliteDatabase(DB_NAME)

class BaseModel(peewee.Model):
    class Meta:
        database = db

class User(BaseModel):
    username = peewee.CharField(unique=True, index=True)
    # 실제 환경에서는 비밀번호를 해시하여 저장해야 합니다.
    hashed_password = peewee.CharField()
    full_name = peewee.CharField(null=True)
    email = peewee.CharField(null=True)

    class Meta:
        # User 테이블 이름을 'user'로 설정
        table_name = 'user'

# --- 5. 사용자 조회 함수 (Peewee 사용) ---
def get_user_by_username(username: str):
    try:
        return User.get(User.username == username)
    except User.DoesNotExist:
        return None

if User.select().count() == 0:
    try:
        User.create(
            username='testuser',
            hashed_password='password123',  # 실제로는 해싱이 필수입니다.
            full_name='Test User',
            email='testuser@[email].com'
        )
        print("INFO: Initial 'testuser' created.")
    except Exception as e:
        print(f"ERROR: Failed to create initial user: {e}")


def update_user_email(username, new_email):
    # 1. 레코드를 불러옵니다.
    user = get_user_by_username(username)
    if not user:
        return False

    # 2. 인스턴스의 속성을 변경합니다.
    user.email = new_email

    # 3. save() 메서드를 호출하여 변경사항을 DB에 반영합니다.
    rows_updated = user.save()  # save()는 업데이트된 레코드의 수를 반환합니다 (보통 1 또는 0)

    if rows_updated > 0:
        print(f"✅ 사용자 정보 수정 성공: {username}의 새 이메일은 {user.email}입니다.")
        return True
    else:
        print(f"⚠️ 사용자 정보 수정 실패: {username}에 변경된 내용이 없습니다.")
        return False


update_user_email("testuser", "new_testuser@[email].com")

def delete_user_by_username(username):
    # 1. 레코드를 불러옵니다. (없으면 DoesNotExist 예외 발생 방지)
    user = User.select().where(User.username == username).get_or_none()

    if not user:
        print(f"❌ 사용자 삭제 실패: Username '{username}'을 찾을 수 없습니다.")
        return False

    # 2. delete_instance() 메서드를 호출하여 삭제합니다.
    rows_deleted = user.delete_instance() # 삭제된 레코드의 수를 반환합니다 (보통 1 또는 0)

    if rows_deleted > 0:
        print(f"✅ 사용자 삭제 성공: Username '{username}' ({rows_deleted}개 레코드 삭제)")
        return True
    else:
        print(f"⚠️ 사용자 삭제 실패: Username '{username}' 레코드가 삭제되지 않았습니다.")
        return False
delete_user_by_username("testuser")
delete_user_by_username("testuser") # 이미 삭제된 사용자 시도 (실패 예시)