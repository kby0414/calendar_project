from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator
from datetime import date as Date
from typing import Optional, Literal

# 사용자가 일정을 생성할 때 지켜야 하는 데이터 규칙 (꾸준히 추가 예정)
class ScheduleCreate(BaseModel):
    title : str = Field(min_length=1, max_length=200)
    date : Date # 기존 API의 date 이름은 유지하되 시작일을 의미합니다.
    end_date : Optional[Date] = None # 생략하면 시작일과 같은 하루짜리 일정
    category : Literal['빨강', '주황', '노랑', '초록', '파랑', '보라', '검정'] = '검정'
    location : Optional[str] = Field(default=None, max_length=300)
    latitude : Optional[float] = None # 위도 (좌표값이라 소수점까지 필요해서 float 사용)
    longitude : Optional[float] = None # 경도 (좌표값이라 소수점까지 필요해서 float 사용)

    # 브라우저 검증만으로는 API 직접 호출을 막을 수 없어 서버에서도 검사합니다.
    @field_validator('title', 'category', 'location', mode='before')
    @classmethod
    def trim_text(cls, value):
        return value.strip() if isinstance(value, str) else value

    @field_validator('date', 'end_date')
    @classmethod
    def validate_calendar_date(cls, value):
        if value is not None and not 2 <= value.year <= 9998:
            raise ValueError('일정 날짜는 0002년부터 9998년까지 입력해주세요.')
        return value

    @model_validator(mode='after')
    def validate_period(self):
        if self.end_date is None:
            self.end_date = self.date
        if self.end_date < self.date:
            raise ValueError('종료일은 시작일과 같거나 이후여야 합니다.')
        return self

# 고유 번호(id)를 불러오기 위한 조회용 데이터 규칙
class ScheduleResponse(ScheduleCreate):
    id : int
    # 기존 DB의 '개인/학습' 같은 분류도 조회는 유지합니다. 화면은 검정으로 표시하고
    # 사용자가 수정할 때 새 색상 분류로 저장하므로 원본 데이터를 일괄 덮어쓰지 않습니다.
    category : str

    model_config = ConfigDict(from_attributes=True)
