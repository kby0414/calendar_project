from fastapi import APIRouter, Depends
import calendar
import datetime
from sqlalchemy.orm import Session

# 최상위 폴더에 있는 파일들 불러오기
from database import get_db
from models import Schedule

# ==========================================
# 기본 및 달력 조회 API
# ==========================================

# APIRouter 객체 생성 (기본 주소를 /calendar로 고정)
router = APIRouter(
    prefix='/calendar',
    tags = ['Calendar']
)

# main.py에서 사용한 @app.get 대신 @router.get 사용함 prefix 덕분에 주소가 짧아짐
# 특정 연/월의 달력 배열(7x6) 생성 API -> 기획서 반영해서 7x6 그리드 자동 월 전환 및 빈칸 처리
@router.get('/{year}/{month}')
def get_calendar(year : int, month : int, db : Session = Depends(get_db)):
    # 일요일을 한 주의 시작으로 설정 (0: 월요일 ~ 6: 일요일)
    cal = calendar.Calendar(firstweekday = 6)
    # 해당 연/월의 달력 데이터를 날짜 객체(date) 형식으로 주 단위로 가져옴
    # monthdatescalendar : 이전 달 끝부분과 다음 달의 시작부분 날짜가 자동으로 포함됨
    month_dates = cal.monthdatescalendar(year, month)

    # 7x6 (총 42칸) 행렬 구조를 맞추기 위해 배열 길이가 6주가 안 되면 0으로 채운 주를 추가 -> 0에서 다음 주를 계산해서 추가로 변경
    while len(month_dates) < 6:
        # 현재 생성된 마지막 주의 마지막 날짜를 구함
        last_day = month_dates[-1][-1]
        # 그 다음 날부터 7일치의 날짜를 계산하여 새로운 주로 추가
        next_week = [last_day + datetime.timedelta(day = i) for i in range(1, 8)]
        month_dates.append(next_week)

    # 달력 표에 표시되는 전체 42일의 시작 날짜와 끝 날짜 파악
    start_date = month_dates[0][0]
    end_date = month_dates[-1][-1]

    # DB에서 해당 기간 (start_date ~ end_date) 사이의 모든 일정 조회
    schedules = db.query(Schedule).filter(
        Schedule.date >= start_date,
        Schedule.date <= end_date
    ).all()

    # 날짜별로 일정을 묶어주는 딕셔너리 생성 ({'2026-08-10' : [일정1, 일정2, ...]})
    schedule_map = {}
    for schedule in schedules:
        date_str = str(schedule.date)
        if date_str not in schedule_map:
            schedule_map[date_str] = []
        schedule_map[date_str].append({
            'id' : schedule.id,
            'title' : schedule.title,
            'category' : schedule.category,
            'location' : schedule.location, # 장소 이름
            'latitude' : schedule.latitude, # 위도
            'longitude' : schedule.longitude # 경도
        })

    grid = []
    for week in month_dates:
        week_data = []
        for d in week:
            date_str = str(d) # 달력 그리드 각 칸에 해당 날짜의 일정을 매핑

            # 이 날짜가 이번 달인지, 이전 달인지, 다음 달인지 판별 (추후 프론트엔드에서 색상 변경에 사용)
            if d.year == year and d.month == month:
                day_type = 'current'
            elif (d.year < year) or (d.year == year and d.month < month):
                day_type = 'prev'
            else:
                day_type = 'next'

            week_data.append({
                'date' : date_str,  # 예 ) '2026-08-01' (전체 날짜, DB 조회 시 사용)
                'day' : d.day,    # 예 ) 1 (달력 칸에 표시될 숫자)
                'type' : day_type, # 예 ) 'current', 'prev', 'next' (회색 처리 등 UI/UX용)
                'schedules' : schedule_map.get(date_str, []) # DB에서 해당 날짜에 맞는 일정을 가져오고, 없으면 빈 리스트 [] 할당
            })
        grid.append(week_data)

    return {
        'year' : year,
        'month' : month,
        'grid' : grid
    }