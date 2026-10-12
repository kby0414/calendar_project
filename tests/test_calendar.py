import calendar
import os
import unittest
from datetime import date, timedelta

os.environ.setdefault('DATABASE_URL', 'sqlite:///:memory:')

from sqlalchemy import create_engine
from sqlalchemy.orm import Session

from models import Base, Schedule
from routers.calendar import get_calendar


class CalendarTests(unittest.TestCase):
    def setUp(self):
        self.engine = create_engine('sqlite:///:memory:')
        Base.metadata.create_all(self.engine)
        self.db = Session(self.engine)

    def tearDown(self):
        self.db.close()
        self.engine.dispose()

    def test_all_months_have_42_consecutive_days_starting_monday(self):
        for year in (2024, 2026):
            for month in range(1, 13):
                with self.subTest(year=year, month=month):
                    grid = get_calendar(year, month, self.db)['grid']
                    self.assertEqual([len(week) for week in grid], [7] * 6)
                    cells = [cell for week in grid for cell in week]
                    dates = [date.fromisoformat(cell['date']) for cell in cells]
                    self.assertEqual(dates[0].weekday(), 0)
                    self.assertEqual(dates, [dates[0] + timedelta(days=i) for i in range(42)])
                    current = [cell['day'] for cell in cells if cell['type'] == 'current']
                    self.assertEqual(current, list(range(1, calendar.monthrange(year, month)[1] + 1)))

    def test_supported_year_boundaries(self):
        for year, month in ((1, 1), (9998, 12)):
            grid = get_calendar(year, month, self.db)['grid']
            self.assertEqual(sum(map(len, grid)), 42)

    def test_schedules_include_adjacent_months_only_within_grid(self):
        for day, title in ((date(2026, 9, 27), 'outside'),
                           (date(2026, 9, 28), 'previous'),
                           (date(2026, 10, 7), 'current'),
                           (date(2026, 11, 8), 'next'),
                           (date(2026, 11, 9), 'outside')):
            self.db.add(Schedule(title=title, date=day, category='test'))
        self.db.commit()
        cells = [cell for week in get_calendar(2026, 10, self.db)['grid'] for cell in week]
        shown = [(cell['date'], item['title']) for cell in cells for item in cell['schedules']]
        self.assertEqual(shown, [('2026-09-28', 'previous'), ('2026-10-07', 'current'), ('2026-11-08', 'next')])


if __name__ == '__main__':
    unittest.main()
