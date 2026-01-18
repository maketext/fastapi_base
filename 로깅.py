from fastapi import FastAPI, Request
from datetime import datetime, timezone, timedelta
import logging

app = FastAPI()

logger = logging.getLogger("access_log11")

logger.setLevel(logging.INFO)
handler = logging.FileHandler("access.log")
formatter = logging.Formatter('%(message)s')
handler.setFormatter(formatter)
logger.addHandler(handler)

"""
log_format_fields = [
    "%(asctime)s",      # 로그 발생 시간
    "%(levelname)s",    # 로그 레벨 (INFO, DEBUG, etc.)
    "%(name)s",         # 로거 이름
    "%(message)s",      # 실제 로그 메시지
    "%(filename)s",     # 로그를 남긴 파일 이름
    "%(funcName)s",     # 로그를 남긴 함수 이름
    "%(lineno)d",       # 로그를 남긴 코드 줄 번호
    "%(module)s",       # 모듈 이름
    "%(pathname)s",     # 전체 파일 경로
    "%(process)d",      # 프로세스 ID
    "%(thread)d",       # 스레드 ID
    "%(threadName)s"    # 스레드 이름
]
"""

@app.middleware("http")
async def log_requests(request: Request, call_next):
    KST = timezone(timedelta(hours=9))
    start_time = datetime.now(KST)
    timestamp = start_time.strftime("%d/%b/%Y:%H:%M:%S %z")
    client_host = request.client.host
    method = request.method
    path = request.url.path
    user_agent = request.headers.get("user-agent", "-")

    log_format = f'{client_host} - - [{timestamp}] "{method} {path} HTTP/1.1" - - "{user_agent}"'
    logger.info(log_format)

    response = await call_next(request)
    return response


@app.get("/")
async def sample_endpoint():
    return None
















