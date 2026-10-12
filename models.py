from sqlalchemy import Column, Integer, String, Date, Float
from database import Base

# 기획서 기준 : 일정 저장을 위한 테이블 모델 정의 - 변경가능성 있음
class Schedule(Base):
    __tablename__ = 'schedules'

    id = Column(Integer, primary_key = True, index = True) 
    title = Column(String, index = True) # 일정 제목이나 내용
    date = Column(Date, index = True) # 일정 날짜
    # date는 시작일입니다. 하루마다 복제하지 않고 하나의 id에 기간을 저장해야
    # 어느 날짜에서 수정/삭제해도 기간 전체에 동일하게 반영됩니다.
    end_date = Column(Date, nullable=True) # 기존 일정의 NULL은 시작일과 같은 하루로 해석
    category = Column(String, index = True) # 빨강/주황/노랑/초록/파랑/보라/검정
    location = Column(String, nullable = True) # 장소 이름
    latitude = Column(Float, nullable= True) # 위도
    longitude = Column(Float, nullable= True) # 경도
