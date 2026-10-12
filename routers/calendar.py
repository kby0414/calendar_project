from fastapi import APIRouter, Depends, Path
import calendar
import datetime
from sqlalchemy.orm import Session
from sqlalchemy import func

# 최상위 폴더에 있는 파일들 불러오기
from database import get_db
from models import Schedule
from holiday_calendar import get_holiday_data

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
def get_calendar(
    year: int = Path(..., ge=2, le=9998),
    month: int = Path(..., ge=1, le=12),
    db: Session = Depends(get_db),
):
    # 일요일 시작(6)으로 헤더와 데이터 순서를 함께 변경합니다.
    # 1년 1월은 앞달 날짜가 0년이 되므로 앞뒤 연도가 존재하는 2~9998년만 받습니다.
    cal = calendar.Calendar(firstweekday = 6)
    # 해당 연/월의 달력 데이터를 날짜 객체(date) 형식으로 주 단위로 가져옴
    # monthdatescalendar : 이전 달 끝부분과 다음 달의 시작부분 날짜가 자동으로 포함됨
    month_dates = cal.monthdatescalendar(year, month)

    # 7x6 (총 42칸) 행렬 구조를 맞추기 위해 배열 길이가 6주가 안 되면 0으로 채운 주를 추가 -> 0에서 다음 주를 계산해서 추가로 변경
    while len(month_dates) < 6:
        # 현재 생성된 마지막 주의 마지막 날짜를 구함
        last_day = month_dates[-1][-1]
        # 그 다음 날부터 7일치의 날짜를 계산하여 새로운 주로 추가
        next_week = [last_day + datetime.timedelta(days = i) for i in range(1, 8)]
        month_dates.append(next_week)

    # 달력 표에 표시되는 전체 42일의 시작 날짜와 끝 날짜 파악
    start_date = month_dates[0][0]
    end_date = month_dates[-1][-1]
    holidays, holiday_info = get_holiday_data(start_date, end_date)

    # DB에서 해당 기간 (start_date ~ end_date) 사이의 모든 일정 조회
    schedules = db.query(Schedule).filter(
        Schedule.date <= end_date,
        func.coalesce(Schedule.end_date, Schedule.date) >= start_date,
    ).order_by(Schedule.date, Schedule.id).all()

    # 날짜별로 일정을 묶어주는 딕셔너리 생성 ({'2026-08-10' : [일정1, 일정2, ...]})
    schedule_map = {}
    for schedule in schedules:
        schedule_end = schedule.end_date or schedule.date
        item = {
            'id' : schedule.id,
            'date': schedule.date.isoformat(),
            'end_date': schedule_end.isoformat(),
            'title' : schedule.title,
            'category' : schedule.category,
            'location' : schedule.location, # 장소 이름
            'latitude' : schedule.latitude, # 위도
            'longitude' : schedule.longitude # 경도
        }
        # 시작일～종료일을 모두 포함합니다. 기간이 길어도 현재 42칸만 펼쳐서
        # 이전 달에서 시작한 일정과 다음 달까지 이어지는 일정을 빠짐없이 표시합니다.
        visible_start = max(schedule.date, start_date)
        visible_end = min(schedule_end, end_date)
        for offset in range((visible_end - visible_start).days + 1):
            date_str = (visible_start + datetime.timedelta(days=offset)).isoformat()
            schedule_map.setdefault(date_str, []).append(item)

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
                # 공휴일은 개인 일정이 아니므로 별도 필드로 제공합니다.
                'holidays': holidays.get(date_str, []),
                'schedules' : schedule_map.get(date_str, []) # DB에서 해당 날짜에 맞는 일정을 가져오고, 없으면 빈 리스트 [] 할당
            })
        grid.append(week_data)

    return {
        'year' : year,
        'month' : month,
        'holiday_info': holiday_info,
        'grid' : grid
    }
