import os
import unittest
from datetime import date

os.environ.setdefault('DATABASE_URL', 'sqlite:///:memory:')

from pydantic import ValidationError
from sqlalchemy import create_engine, text, inspect
from sqlalchemy.orm import Session
from models import Base, Schedule
from schemas import ScheduleCreate, ScheduleResponse
from routers.schedules import create_schedule, update_schedule, delete_schedule
from routers.calendar import get_calendar
from migrations import ensure_schedule_period_column


class PeriodTests(unittest.TestCase):
    def setUp(self):
        self.engine = create_engine('sqlite:///:memory:')
        Base.metadata.create_all(self.engine)
        self.db = Session(self.engine)

    def tearDown(self):
        self.db.close()
        self.engine.dispose()

    def shown(self, year, month, ident):
        return {cell['date']: item for week in get_calendar(year, month, self.db)['grid']
                for cell in week for item in cell['schedules'] if item['id'] == ident}

    def test_inclusive_period_edit_shrink_and_delete(self):
        payload = ScheduleCreate(title='기간 일정', date='2026-10-12', end_date='2026-10-15', category='빨강')
        ident = create_schedule(payload, self.db)['data'].id
        shown = self.shown(2026, 10, ident)
        self.assertEqual(list(shown), ['2026-10-12', '2026-10-13', '2026-10-14', '2026-10-15'])
        self.assertEqual(self.db.query(Schedule).count(), 1)
        # 14일에 표시된 id와 원래 시작일로 수정해도 전체 기간이 바뀝니다.
        middle = shown['2026-10-14']
        self.assertEqual(middle['date'], '2026-10-12')
        update_schedule(middle['id'], ScheduleCreate(title='전체 수정', date=middle['date'],
                        end_date='2026-10-14', category='보라'), self.db)
        shown = self.shown(2026, 10, ident)
        self.assertEqual(len(shown), 3)
        self.assertTrue(all(item['title'] == '전체 수정' and item['category'] == '보라' for item in shown.values()))
        self.assertNotIn('2026-10-15', shown)
        delete_schedule(shown['2026-10-13']['id'], self.db)
        self.assertEqual(self.shown(2026, 10, ident), {})

    def test_cross_month_year_and_full_grid_overlap(self):
        item = create_schedule(ScheduleCreate(title='연말', date='2026-12-30', end_date='2027-01-03', category='파랑'), self.db)['data']
        self.assertEqual(len(self.shown(2026, 12, item.id)), 5)
        self.assertEqual(len(self.shown(2027, 1, item.id)), 5)
        update_schedule(item.id, ScheduleCreate(title='장기', date='2026-01-01', end_date='2027-12-31', category='초록'), self.db)
        self.assertEqual(len(self.shown(2026, 10, item.id)), 42)

    def test_single_day_legacy_and_leap_day(self):
        legacy = Schedule(title='기존 일정', date=date(2026, 10, 12), category='개인')
        self.db.add(legacy)
        self.db.commit()
        self.assertEqual(len(self.shown(2026, 10, legacy.id)), 1)
        self.assertEqual(ScheduleResponse.model_validate(legacy).end_date, legacy.date)
        payload = ScheduleCreate(title='윤년', date='2024-02-28', end_date='2024-03-01', category='노랑')
        item = create_schedule(payload, self.db)['data']
        self.assertEqual(list(self.shown(2024, 2, item.id)), ['2024-02-28', '2024-02-29', '2024-03-01'])
        self.assertEqual(ScheduleCreate(title='하루', date='2026-10-12', category='검정').end_date, date(2026, 10, 12))

    def test_invalid_period_and_colors(self):
        base = {'title': '기간', 'date': '2026-10-12', 'category': '검정'}
        for change in ({'end_date': '2026-10-11'}, {'end_date': '9999-01-01'}, {'category': '개인'}, {'category': '#ff0000'}):
            with self.subTest(change=change), self.assertRaises(ValidationError):
                ScheduleCreate(**(base | change))
        for color in ['빨강', '주황', '노랑', '초록', '파랑', '보라', '검정']:
            self.assertEqual(ScheduleCreate(**(base | {'category': color})).category, color)


class MigrationTests(unittest.TestCase):
    def test_additive_upgrade_is_repeatable_and_preserves_old_rows(self):
        engine = create_engine('sqlite:///:memory:')
        try:
            with engine.begin() as connection:
                connection.execute(text('CREATE TABLE schedules (id INTEGER PRIMARY KEY, title VARCHAR, date DATE, category VARCHAR)'))
                connection.execute(text("INSERT INTO schedules VALUES (7, '기존 일정', '2026-10-12', '개인')"))
            ensure_schedule_period_column(engine)
            ensure_schedule_period_column(engine)
            self.assertIn('end_date', {column['name'] for column in inspect(engine).get_columns('schedules')})
            with engine.connect() as connection:
                row = connection.execute(text('SELECT * FROM schedules')).one()
                self.assertEqual(tuple(row), (7, '기존 일정', '2026-10-12', '개인', None))
        finally:
            engine.dispose()
