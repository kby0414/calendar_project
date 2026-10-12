"""기존 일정 데이터를 보존하는 작은 스키마 업그레이드."""
from sqlalchemy import inspect, text


def ensure_schedule_period_column(engine):
    # create_all()은 이미 존재하는 테이블에 열을 추가하지 않습니다.
    # end_date만 추가하고 기존 행은 그대로 둡니다. NULL은 조회 시 date로 대체합니다.
    columns = {column['name'] for column in inspect(engine).get_columns('schedules')}
    if 'end_date' in columns:
        return
    with engine.begin() as connection:
        optional = 'IF NOT EXISTS ' if engine.dialect.name == 'postgresql' else ''
        connection.execute(text(f'ALTER TABLE schedules ADD COLUMN {optional}end_date DATE'))
