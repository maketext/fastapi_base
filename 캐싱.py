#pip install fastapi-cache2
from fastapi import FastAPI
from fastapi_cache import FastAPICache
from fastapi_cache.backends.inmemory import InMemoryBackend
from fastapi_cache.decorator import cache
import time

app = FastAPI()

@app.on_event("startup")
async def startup():
    # Redis 설치 없이 메모리만 사용하도록 설정
    FastAPICache.init(InMemoryBackend())

@app.get("/test-cache")
@cache(expire=10) # 10초 동안 캐싱
async def get_data():
    # 캐싱 확인을 위해 현재 시간을 포함하여 반환
    # 10초 안에는 계속 같은 결과가 나옵니다.
    current_time = time.strftime("%H:%M:%S")
    return {
        "message": "10초 동안은 값이 변하지 않습니다.",
        "time": current_time
    }