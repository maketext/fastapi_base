from fastapi import FastAPI, HTTPException, status
from pydantic import BaseModel, validator, Field


app = FastAPI()


# {"username": "testuser", "user_id": 1, "bio": "<script>"}
class UserProfile(BaseModel):

    username: str = Field(min_length=3, max_length=50)
    user_id: int
    bio: str

    @validator('bio')
    def prevent_line_breaks11(cls, v):
        if '\n' in v or '\r' in v:
            raise ValueError('줄 바꿈 문자는 bio 필드에 허용되지 않습니다.')

        # 특정 악성 스크립트 패턴을 확인 (매우 간단한 예시)
        if '<script>' in v.lower():
            # 실제 서비스에서는 더 복잡한 정규 표현식 기반의 필터링이 필요
            raise ValueError('악성 스크립트 패턴이 감지되었습니다.')
        return v.strip()


@app.post("/profile")
async def create_profile(profile: UserProfile):
    return {
        "message": f"프로필이 생성되었습니다.",
        "username": profile.username,
        "user_id": profile.user_id,
        "bio_length": len(profile.bio)
    }