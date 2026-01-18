from fastapi import FastAPI, Request
from fastapi.templating import Jinja2Templates
from fastapi.responses import HTMLResponse
from datetime import datetime

app = FastAPI()

templates = Jinja2Templates(directory="templates")

USER_DATA = {
    "username": "<script>alert('CodingPartner');</script>",
    "username2": "undefined onmouseenter=alert(1)",
    "status": "Online",
    "items": [
        {"name": "FastAPI Server", "price": 100},
        {"name": "Peewee DB", "price": 50},
        {"name": "Jinja2 Template", "price": 20}
    ]
}

@app.get("/", response_class=HTMLResponse)
def read_home(request: Request):
    """
    홈 페이지를 렌더링하고 데이터를 전달합니다.
    """
    # 템플릿에 전달할 컨텍스트 딕셔너리
    context = {
        # 'request': request는 Jinja2Templates 사용 시 필수입니다!
        "request": request,

        # 실제 데이터
        "title": "Jinja2 통합 홈",
        "user": USER_DATA,
        "current_time": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    }
    # templates.TemplateResponse(템플릿 파일 이름, 컨텍스트 딕셔너리)
    return templates.TemplateResponse("home-xss.html", context)
















