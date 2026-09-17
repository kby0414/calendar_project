from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

# 최상위 폴더에 있는 파일들 불러오기
from database import get_db
from models import Schedule
import schemas
import services

# ==========================================
# 일정 관리 CRUD API
# ==========================================

# APIRouter 객체 생성 ( 기본 주소를 /schedules로 고정)
router = APIRouter(
    prefix = '/schedules',
    tags = ['Schedules']
)

# [C] 생성 (Create) - 일정 저장
@router.post('/')
def create_schedule(schedule: schemas.ScheduleCreate, db: Session = Depends(get_db)):

    lat = schedule.latitude
    lon = schedule.longitude

    # 위도, 경도 값이 없거나 0인 경우 자동으로 입력 (네이버 API 사용)
    if schedule.location and (lat is None or lon is None or lat == 0 or lon == 0):
        lat, lon = services.get_lat_lng(schedule.location)

    # Pydantic으로 검증이 끝난 데이터를 DB 테이블(Schedule) 형식으로 변환
    db_schedule = Schedule(
        title = schedule.title,
        date = schedule.date,
        category = schedule.category,
        location = schedule.location, # 장소 이름
        latitude = lat, # 위도
        longitude = lon # 경도
    )
    # 변환된 데이터를 DB에 추가하고 저장(commit)
    db.add(db_schedule)
    db.commit()
    # DB에 잘 들어갔는지 최신 상태로 새로고침 (DB가 부여한 id값 등을 가져옴)
    db.refresh(db_schedule)
    
    return {'message': '일정이 성공적으로 저장되었습니다!', 'data': db_schedule}


# [R] 읽기 (Read) - 전체 일정 조회
@router.get('/', response_model=list[schemas.ScheduleResponse])
def read_schedules(db: Session = Depends(get_db)):
    # DB의 Schedule 테이블에 있는 모든 데이터를 조회하여 반환
    schedules = db.query(Schedule).all()
    return schedules


# [U] 수정 (Update) - 특정 일정 수정
@router.put('/{schedule_id}')
def update_schedule(schedule_id: int, schedule: schemas.ScheduleCreate, db: Session = Depends(get_db)):
    # 1. 수정하려는 번호(id)의 일정이 DB에 있는지 검색
    db_schedule = db.query(Schedule).filter(Schedule.id == schedule_id).first()
    
    # 2. 만약 해당 번호의 일정이 없다면 404 에러 반환
    if db_schedule is None:
        raise HTTPException(status_code=404, detail="일정을 찾을 수 없습니다.")
    # 3. 일정이 있다면 사용자가 새로 입력한 데이터로 기존 내용 덮어쓰기

    lat = schedule.latitude
    lon = schedule.longitude

    # 위도, 경도 값이 없거나 0인 경우 자동으로 입력 (네이버 API 사용)
    if schedule.location and (lat is None or lon is None or lat == 0 or lon == 0):
        lat, lon = services.get_lat_lng(schedule.location)

    db_schedule.title = schedule.title
    db_schedule.date = schedule.date
    db_schedule.category = schedule.category
    db_schedule.location = schedule.location # 장소 이름
    db_schedule.latitude = lat # 위도 
    db_schedule.longitude = lon # 경도 
    
    # 4. 변경된 사항을 DB에 확정(commit)하고 최신 상태로 새로고침
    db.commit()
    db.refresh(db_schedule)

    return {'message': f'{schedule_id}번 일정이 성공적으로 수정되었습니다!', 'data': db_schedule}


# [D] 삭제 (Delete) - 특정 일정 삭제
@router.delete('/{schedule_id}')
def delete_schedule(schedule_id: int, db: Session = Depends(get_db)):
    # 1. 지우려는 번호(id)의 일정이 DB에 있는지 검색
    db_schedule = db.query(Schedule).filter(Schedule.id == schedule_id).first()
    
    # 2. 만약 해당 번호의 일정이 없다면 404 에러 반환
    if db_schedule is None:
        raise HTTPException(status_code=404, detail="일정을 찾을 수 없습니다.")
    
    # 3. 일정이 있다면 DB에서 삭제하고 확실히 적용(commit)
    db.delete(db_schedule)
    db.commit()
    
    return {'message': f'{schedule_id}번 일정이 성공적으로 삭제되었습니다!'}