"""
tests/test_utils.py

B-01: app.utils.get_deadline_status() 境界値テスト。

テスト仕様書 書類No.（未割当）の単体テスト対象：
  - None        → None  （未点検）
  - 昨日        → 'overdue'
  - 今日        → 'soon'
  - 6日後       → 'soon'
  - 7日後       → 'soon'（境界値：まもなく上限）
  - 8日後       → 'normal'（境界値：正常開始）
  - 30日後      → 'normal'
"""

import pytest
from datetime import date, timedelta
from app.utils import get_deadline_status


class TestGetDeadlineStatus:
    """get_deadline_status() の境界値テスト（7件）"""

    def test_none_returns_none(self):
        """next_inspection_date が None の場合は None を返す（未点検）"""
        result = get_deadline_status(None)
        assert result is None

    def test_yesterday_returns_overdue(self):
        """昨日の日付を渡すと 'overdue' を返す"""
        yesterday = date.today() - timedelta(days=1)
        result = get_deadline_status(yesterday)
        assert result == "overdue"

    def test_today_returns_soon(self):
        """今日の日付を渡すと 'soon' を返す（残り0日 → まもなく）"""
        result = get_deadline_status(date.today())
        assert result == "soon"

    def test_six_days_later_returns_soon(self):
        """6日後の日付を渡すと 'soon' を返す"""
        six_days_later = date.today() + timedelta(days=6)
        result = get_deadline_status(six_days_later)
        assert result == "soon"

    def test_seven_days_later_returns_soon(self):
        """7日後の日付を渡すと 'soon' を返す（まもなくの上限境界値）"""
        seven_days_later = date.today() + timedelta(days=7)
        result = get_deadline_status(seven_days_later)
        assert result == "soon"

    def test_eight_days_later_returns_normal(self):
        """8日後の日付を渡すと 'normal' を返す（正常の開始境界値）"""
        eight_days_later = date.today() + timedelta(days=8)
        result = get_deadline_status(eight_days_later)
        assert result == "normal"

    def test_thirty_days_later_returns_normal(self):
        """30日後の日付を渡すと 'normal' を返す"""
        thirty_days_later = date.today() + timedelta(days=30)
        result = get_deadline_status(thirty_days_later)
        assert result == "normal"
