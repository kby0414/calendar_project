from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.orm import declarative_base
from settings import DATABASE_URL

# PostgreSQL 연결 정보
# 형식: postgresql://사용자이름:비밀번호@호스트:포트/데이터베이스이름
SQLALCHEMY_DATABASE_URL = DATABASE_URL

# DB 엔진 및 세션 생성
engine = create_engine(SQLALCHEMY_DATABASE_URL, pool_pre_ping=True, connect_args={"connect_timeout": 5})
SessionLocal = sessionmaker(autocommit = False, autoflush = False, bind = engine)

Base = declarative_base()

# main.py에 있던 DB 세션 생성 함수 이동 (리팩토링)
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
