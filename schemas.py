from pydantic import BaseModel
from datetime import date
from typing import Optional # 선택 사항을 만들기 위해 추가

# 사용자가 일정을 생성할 때 지켜야 하는 데이터 규칙 (꾸준히 추가 예정)
class ScheduleCreate(BaseModel):
    title : str # 일정 제목은 문자 (텍스트)여야 함
    date : date # 날짜는 연-월-일 형식이여야 함
    category : str # 추후 지도 학습 모델로 자동 분류할 타겟 (업무, 개인 등)도 문자 여야 함
    location : Optional[str] = None # 장소 정보 (입력 안 하면 None값)
    latitude : Optional[float] = None # 위도 (좌표값이라 소수점까지 필요해서 float 사용)
    longitude : Optional[float] = None # 경도 (좌표값이라 소수점까지 필요해서 float 사용)

# 고유 번호(id)를 불러오기 위한 조회용 데이터 규칙
class ScheduleResponse(ScheduleCreate):
    id : int

    class Config:
        from_attributes = True # DB 모델(SQLAlchemy)을 Pydantic 데이터로 원활하게 변환해주는 설정