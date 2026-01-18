from abc import ABC, abstractmethod
from fastapi import FastAPI, Depends


# 1. [Port] - 인터페이스 (추상 클래스)
# 비즈니스 로직이 외부 세계에 요구하는 명세입니다.
class UserRepositoryPort(ABC):
    @abstractmethod
    def save(self, name: str) -> str:
        pass

# 2. [Adapter] - 구현체 (MySQL 어댑터)
# 포트의 명세를 실제로 구현합니다.
class MySQLUserRepositoryAdapter(UserRepositoryPort):
    def save(self, name: str) -> str:
        # 실제로는 DB 저장 로직이 들어갑니다.


        return f"MySQL에 '{name}' 저장 완료!"

# 3. [Adapter] - 구현체 (메모리 어댑터 / 테스트용)
class MemoryUserRepositoryAdapter(UserRepositoryPort):
    def save(self, name: str) -> str:
        return f"메모리에 '{name}' 임시 저장!"

# 4. [Service] - 비즈니스 로직
# 특정 어댑터가 아닌 '포트(인터페이스)'에 의존합니다.
class UserService:
    def __init__(self, repo: UserRepositoryPort):
        self.repo = repo

    def register_user(self, name: str):
        return self.repo.save(name)

# --- 주입(Injection) 설정 ---

app = FastAPI()

# 스프링의 컴포넌트 스캔 대신, 수동으로 구현체를 선택하여 주입하는 함수입니다.
def get_user_service() -> UserService:
    # 여기서 원하는 어댑터를 선택합니다. (전략 패턴)
    # 나중에 MySQL 대신 다른 걸로 바꾸고 싶다면 여기만 수정하면 됩니다.
    #repository_adapter = MySQLUserRepositoryAdapter()
    repository_adapter = MemoryUserRepositoryAdapter()
    return UserService(repository_adapter)

# 5. [Controller] - API 엔드포인트
@app.post("/users")
def create_user(name: str, service: UserService = Depends(get_user_service)):
    test1 = Depends(get_user_service)
    return {"result": service.register_user(name)}










