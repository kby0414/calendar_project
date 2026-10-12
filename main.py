from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware # CORS 설정 도구
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from pathlib import Path
from database import engine
import models
from migrations import ensure_schedule_period_column

from routers import calendar, schedules

# ==========================================
# 초기 세팅 및 DB 연결
# ==========================================

# 서버 실행 시 database.py에 정의된 테이블(schedules)을 DB에 생성
models.Base.metadata.create_all(bind = engine)
ensure_schedule_period_column(engine)

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

# 화면과 API를 같은 서버에서 제공합니다. 브라우저에서는 '/'로 달력에 접속합니다.
# __file__ 기준 절대경로를 써야 다른 폴더에서 실행해도 CSS/JS 파일을 찾을 수 있습니다.
FRONTEND_DIR = Path(__file__).resolve().parent / 'frontend'
app.mount('/static', StaticFiles(directory=FRONTEND_DIR), name='static')

@app.get('/', include_in_schema=False)
def read_root():
    return FileResponse(FRONTEND_DIR / 'index.html')
