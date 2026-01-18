from fastapi import FastAPI, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from jose import JWTError, jwt
from datetime import datetime, timedelta
from typing import Optional
from peewee import *  # Peewee 임포트
import os
from dotenv import load_dotenv
from pathlib import Path

# config.env 파일 경로를 명시적으로 지정
CONFIG_ENV_FILE = "config.env"
env_path = Path(__file__).parent / CONFIG_ENV_FILE
load_dotenv(dotenv_path=env_path)

# --- 1. Peewee DB 설정 및 모델 정의 ---
# SQLite 데이터베이스 파일을 설정합니다.
DB_NAME = os.getenv("DB_NAME", "your_database_name")
SECRET_KEY = os.getenv("SECRET_KEY", "your-super-secret-key")  # 이 부분을 반드시 변경하세요!

with open(CONFIG_ENV_FILE, "w", encoding="utf-8") as f:
    f.write("\n".join(["DB_NAME=1", "SECRET_KEY=1"]))

print("DB_NAME", DB_NAME)
print("SECRET_KEY", SECRET_KEY)

db = SqliteDatabase(DB_NAME)

class BaseModel(Model):
    class Meta:
        database = db

class User(BaseModel):
    username = CharField(unique=True, index=True)
    # 실제 환경에서는 비밀번호를 해시하여 저장해야 합니다.
    hashed_password = CharField()
    full_name = CharField(null=True)
    email = CharField(null=True)

    class Meta:
        # User 테이블 이름을 'user'로 설정
        table_name = 'user'

    # --- 2. 보안 설정 (기존과 동일) ---

SECRET_KEY = SECRET_KEY
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 30

# --- 3. JWT 유틸리티 함수 (기존과 동일) ---
def create_access_token(data: dict, expires_delta: Optional[timedelta] = None):
    to_encode = data.copy()

    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)

    to_encode.update({"exp": expire})

    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt

def decode_access_token(token: str):
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        return payload
    except JWTError:
        return None

# --- 4. DB 연결/해제 의존성 함수 ---
def get_db():
    """
    FastAPI 요청이 들어올 때마다 DB를 열고, 응답 후 닫도록 합니다.
    FastAPI의 `yield`를 사용한 의존성입니다.
    """
    if db.is_closed():
        db.connect()
    try:
        yield  # 이 시점에 라우트 함수가 실행됩니다.
    finally:
        if not db.is_closed():
            db.close()

# --- 5. 사용자 조회 함수 (Peewee 사용) ---
def get_user_by_username(username: str):
    try:
        return User.get(User.username == username)
    except User.DoesNotExist:
        return None

# --- 6. JWT 인증 의존성 함수 (Peewee 통합) ---
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="login")

# `get_db`를 Depends에 추가하여 요청당 DB 연결을 보장합니다.
def get_current_user(token: str = Depends(oauth2_scheme), db_conn: None = Depends(get_db)):
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )

    payload = decode_access_token(token)
    if payload is None:
        raise credentials_exception

    username: str = payload.get("sub")
    if username is None:
        raise credentials_exception

    # 데이터베이스에서 사용자 정보를 조회합니다. (Peewee 사용)
    user = get_user_by_username(username)
    if user is None:
        raise credentials_exception

    # Peewee 모델 객체 대신, 필요한 정보를 딕셔너리로 반환합니다.
    return {"username": user.username, "full_name": user.full_name}

app = FastAPI()

@app.on_event("startup")
def startup():
    """
    FastAPI 서버 시작 시 DB 연결 및 테이블 생성을 시도합니다.
    """
    db.connect()
    # User 테이블이 없으면 생성합니다.
    db.create_tables([User], safe=True)

    # 초기 테스트 사용자 추가 (데이터베이스가 비어 있을 경우)
    if User.select().count() == 0:
        try:
            User.create(
                username='testuser',
                hashed_password='password123',  # 실제로는 해싱이 필수입니다.
                full_name='Test User',
                email='test@peewee.com'
            )
            print("INFO: Initial 'testuser' created.")
        except Exception as e:
            print(f"ERROR: Failed to create initial user: {e}")

@app.on_event("shutdown")
def shutdown():
    """
    FastAPI 서버 종료 시 DB 연결을 닫습니다.
    """
    if not db.is_closed():
        db.close()
    with open(CONFIG_ENV_FILE, "w", encoding="utf-8") as f:
        f.write("\n".join([f"DB_NAME={DB_NAME}", f"SECRET_KEY={SECRET_KEY}"]))

# --- 8. 라우트 정의 (Peewee 통합) ---

@app.post("/login")
# DB 연결 의존성을 추가합니다.
def login_for_access_token(form_data: OAuth2PasswordRequestForm = Depends(), db_conn: None = Depends(get_db)):
    user = get_user_by_username(form_data.username)

    # Peewee를 통해 조회된 사용자 정보와 비밀번호 비교
    if not user or user.hashed_password != form_data.password:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )

    access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        data={"sub": user.username}, expires_delta=access_token_expires
    )
    return {"access_token": access_token, "token_type": "bearer"}

@app.get("/public")
def read_public_data():
    return {"message": "이것은 누구나 접근 가능한 공용 데이터입니다."}


@app.get("/protected")
# JWT 및 DB 연결 의존성을 사용합니다.
def read_protected_data(current_user: dict = Depends(get_current_user)):
    return {
        "message": "이것은 인증된 사용자만 접근 가능한 보호된 데이터입니다. (DB 연동 확인)",
        "user": current_user["username"]
    }









