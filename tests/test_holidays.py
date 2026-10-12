import unittest
from datetime import date
from holiday_calendar import get_holiday_data


class HolidayTests(unittest.TestCase):
    def test_naver_public_holidays_and_substitutes(self):
        days, info = get_holiday_data(date(2026, 1, 1), date(2026, 12, 31))
        self.assertEqual(days['2026-10-03'], ['개천절'])
        self.assertEqual(days['2026-10-05'], ['대체공휴일(개천절)'])
        self.assertEqual(days['2026-10-09'], ['한글날'])
        self.assertEqual(days['2026-06-03'], ['전국동시지방선거'])
        self.assertEqual(days['2026-02-17'], ['설날'])
        self.assertEqual(info['missing_years'], [])

    def test_no_anniversaries_or_solar_terms(self):
        days, _ = get_holiday_data(date(2026, 1, 1), date(2026, 12, 31))
        for key in ('2026-04-05', '2026-05-08', '2026-05-15', '2026-10-08'):
            self.assertNotIn(key, days)

    def test_range_filter_and_unknown_year(self):
        days, _ = get_holiday_data(date(2026, 10, 4), date(2026, 10, 6))
        self.assertEqual(list(days), ['2026-10-05'])
        days, info = get_holiday_data(date(2030, 1, 1), date(2030, 2, 1))
        self.assertEqual(days, {})
        self.assertEqual(info['missing_years'], [2030])

    def test_next_year_lunar_and_substitute_days(self):
        days, _ = get_holiday_data(date(2027, 1, 1), date(2027, 12, 31))
        self.assertEqual(days['2027-02-07'], ['설날'])
        self.assertEqual(days['2027-02-09'], ['대체공휴일(설날)'])
