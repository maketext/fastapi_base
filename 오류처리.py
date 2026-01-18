from fastapi import FastAPI, Request, status
from fastapi.responses import JSONResponse


app = FastAPI()

@app.exception_handler(ValueError)       # 1. ValueError 처리
@app.exception_handler(TypeError)        # 2. TypeError 처리
@app.exception_handler(KeyError)         # 3. KeyError 처리
async def common_error_handler(request: Request, exc: Exception):
    """
    ValueError, TypeError, KeyError 발생 시 공통으로 처리합니다.
    """

    error_type = type(exc).__name__

    print(f"로그: 요청 URL {request.url} 에서 {error_type} 발생: {exc}")

    return JSONResponse(
        status_code=status.HTTP_400_BAD_REQUEST,
        content={
            "detail": f"데이터 처리 중 오류가 발생했습니다.",
            "error_type": error_type,
            "message": str(exc)
        },
    )


# ----------------------------------------------------
# 테스트 경로 함수
# ----------------------------------------------------

@app.get("/test-error/{error_type}")
async def trigger_error(error_type: str):
    if error_type == "value":
        raise ValueError("잘못된 입력 값입니다.")
    elif error_type == "type":
        # 문자열을 정수와 더할 때 TypeError 발생
        raise TypeError("잘못된 자료형 연산입니다.")
    elif error_type == "key":
        # 딕셔너리에 없는 키에 접근할 때 KeyError 발생
        data = {}
        return data["non_existent_key"]

    return {"status": "OK"}

