"""네이버 달력에서 확인한 공휴일만 읽습니다. 기념일/절기/음력은 포함하지 않습니다."""
import json
from functools import lru_cache
from pathlib import Path


@lru_cache(maxsize=1)
def load_holidays():
    # 웹 요청마다 외부 사이트를 호출하지 않습니다. 확인한 연도별 목록을 버전 관리합니다.
    # 데이터 수정 후 서버를 재시작해야 캐시가 갱신됩니다.
    path = Path(__file__).resolve().parent / 'data' / 'naver_holidays.json'
    return json.loads(path.read_text(encoding='utf-8'))


def get_holiday_data(start, end):
    data = load_holidays()
    missing_years = [year for year in range(start.year, end.year + 1)
                     if year not in data['years']]
    holidays = {key: names for key, names in data['holidays'].items()
                if start.isoformat() <= key <= end.isoformat()}
    # 미확인 연도를 '공휴일 없음'으로 오해하지 않게 화면에 범위를 알려줍니다.
    return holidays, {
        'source': data['source'], 'source_url': data['source_url'],
        'verified_on': data['verified_on'], 'years': data['years'],
        'missing_years': missing_years,
    }
