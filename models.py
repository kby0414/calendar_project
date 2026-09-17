from sqlalchemy import Column, Integer, String, Date, Float
from database import Base

# 기획서 기준 : 일정 저장을 위한 테이블 모델 정의 - 변경가능성 있음
class Schedule(Base):
    __tablename__ = 'schedules'

    id = Column(Integer, primary_key = True, index = True) 
    title = Column(String, index = True) # 일정 제목이나 내용
    date = Column(Date, index = True) # 일정 날짜
    category = Column(String, index = True) # 추후 머신러닝 지도 학습으로 분류될 카테고리 (지금은 그냥 작성란)
    location = Column(String, nullable = True) # 장소 이름
    latitude = Column(Float, nullable= True) # 위도
    longitude = Column(Float, nullable= True) # 경도