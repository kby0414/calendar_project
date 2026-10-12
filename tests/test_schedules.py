import os
import unittest
from unittest.mock import patch

os.environ.setdefault('DATABASE_URL', 'sqlite:///:memory:')

from fastapi import HTTPException
from pydantic import ValidationError
from sqlalchemy import create_engine
from sqlalchemy.orm import Session
from models import Base
from schemas import ScheduleCreate
from routers.schedules import create_schedule, read_schedules, update_schedule, delete_schedule


class ScheduleTests(unittest.TestCase):
    def setUp(self):
        # 실제 PostgreSQL 일정이나 외부 지도 API에 영향을 주지 않는 독립 테스트입니다.
        self.engine = create_engine('sqlite:///:memory:')
        Base.metadata.create_all(self.engine)
        self.db = Session(self.engine)

    def tearDown(self):
        self.db.close()
        self.engine.dispose()

    def test_create_edit_move_delete(self):
        payload = ScheduleCreate(title='  공부  ', date='2026-10-12', category=' 빨강 ')
        item = create_schedule(payload, self.db)['data']
        ident = item.id
        self.assertEqual(item.title, '공부')
        edited = ScheduleCreate(title='수정된 공부', date='2026-11-01', category='파랑',
                                location='서울', latitude=37.5, longitude=127.0)
        with patch('services.get_lat_lng') as geocode:
            item = update_schedule(ident, edited, self.db)['data']
            geocode.assert_not_called()
        self.assertEqual(item.date.isoformat(), '2026-11-01')
        self.assertEqual(item.latitude, 37.5)
        self.assertEqual(len(read_schedules(self.db)), 1)
        delete_schedule(ident, self.db)
        self.assertEqual(read_schedules(self.db), [])
        with self.assertRaises(HTTPException) as caught:
            update_schedule(ident, edited, self.db)
        self.assertEqual(caught.exception.status_code, 404)

    def test_blank_and_oversized_fields_rejected(self):
        for change in ({'title': '  '}, {'category': '  '}, {'title': 'x' * 201},
                       {'category': 'x' * 51}, {'location': 'x' * 301}, {'date': '0001-01-01'}):
            with self.subTest(change=change), self.assertRaises(ValidationError):
                ScheduleCreate(**({'title': '일정', 'date': '2026-10-12', 'category': '검정'} | change))

    def test_geocode_failure_keeps_schedule(self):
        payload = ScheduleCreate(title='약속', date='2026-10-12', category='검정', location='알 수 없는 장소')
        with patch('services.get_lat_lng', return_value=(None, None)):
            item = create_schedule(payload, self.db)['data']
        self.assertEqual(item.location, '알 수 없는 장소')
        self.assertIsNone(item.latitude)
