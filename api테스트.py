from fastapi import FastAPI, Form
from pydantic import BaseModel

app = FastAPI()

# JSON 엔드포인트 (기존과 동일)
class ItemJSON(BaseModel):
    name: str
    price: float

@app.post("/items/json")
async def create_item_json(item: ItemJSON):
    return {"received_type": "JSON", "data": item}

# Form 엔드포인트 (Annotated 없이 작성)
@app.post("/items/form")
async def create_item_form(
    name: str = Form(...),           # ...은 필수값임을 의미합니다.
    price: float = Form(0.0),        # 기본값을 0.0으로 설정
    description: str = Form(None)    # 선택 사항
):
    return {
        "received_type": "Form",
        "data": {
            "name": name,
            "price": price,
            "description": description
        }
    }