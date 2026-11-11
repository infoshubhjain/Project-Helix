import unittest
from datetime import date
from unittest.mock import patch

from Project import check_daily_scraper as monitor


class DailyMonitorTests(unittest.TestCase):
    def test_healthy_scheduled_scrape(self):
        run = {"id": 1, "created_at": "2026-11-11T16:00:00Z", "conclusion": "success"}
        job = {"id": 2, "name": "scrape-and-update", "conclusion": "success"}
        with patch.object(monitor, "get_json", side_effect=[{"workflow_runs": [run]}, {"jobs": [job]}, []]):
            self.assertTrue(monitor.healthy_scheduled_scrape(date(2026, 11, 11)))

    def test_missing_scheduled_scrape(self):
        with patch.object(monitor, "get_json", return_value={"workflow_runs": []}):
            self.assertFalse(monitor.healthy_scheduled_scrape(date(2026, 11, 11)))

    def test_source_warning_is_unhealthy(self):
        run = {"id": 1, "created_at": "2026-11-11T16:00:00Z", "conclusion": "success"}
        job = {"id": 2, "name": "scrape-and-update", "conclusion": "success"}
        warning = {"annotation_level": "warning", "title": "Empty scraper source"}
        with patch.object(monitor, "get_json", side_effect=[{"workflow_runs": [run]}, {"jobs": [job]}, [warning]]):
            self.assertFalse(monitor.healthy_scheduled_scrape(date(2026, 11, 11)))


if __name__ == "__main__":
    unittest.main()
