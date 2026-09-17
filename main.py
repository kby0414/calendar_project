from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware # CORS 설정 도구
from database import engine
import models

from routers import calendar, schedules

# ==========================================
# 초기 세팅 및 DB 연결
# ==========================================

# 서버 실행 시 database.py에 정의된 테이블(schedules)을 DB에 생성
models.Base.metadata.create_all(bind = engine)

# FastAPI 애플리케이션(서버) 객체 생성
app = FastAPI()

# 프론트엔드에서 API를 호출할 수 있도록 CORS 허용 부여
app.add_middleware(
    CORSMiddleware,
    allow_origins = ['*'], # 모든 주소에서 접속 허용
    allow_credentials = True, # 쿠키, 인증 헤더, TLS 클라이언트 요청 허용
    allow_methods = ['*'], # GET, POST, PUT, DELETE 모두 허용
    allow_headers = ['*'], # 모든 데이터 형식 허용
)

# 분리시킨 라우터들 메인 서버에 연결
app.include_router(calendar.router)
app.include_router(schedules.router)

@app.get('/')
def read_root(): # (UI/UX 구성은 나중)
    return {'message': "캘린더 서버 테스트"}