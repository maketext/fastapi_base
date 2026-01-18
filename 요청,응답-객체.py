from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse


app = FastAPI()

@app.get("/info")
def read_root(request: Request):
    # 클라이언트 IP 주소에 접근
    client_host = request.client.host
    # 원시 헤더 정보에 접근
    user_agent = request.headers.get("user-agent")
    return {"client_host": client_host, "user_agent": user_agent}


@app.get("/html-with-header", response_class=HTMLResponse)
def get_html_response():
    html_content = "<html><body><h1>커스텀 헤더가 있는 페이지</h1></body></html>"
    response = HTMLResponse(
        content=html_content,
        status_code=200,
        headers={"X-Custom-Header": "FastAPI-HTML"}  # 헤더 쓰기/설정
    )
    return response