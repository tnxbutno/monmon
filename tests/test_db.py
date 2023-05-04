"""Tests for the `db_connector` module"""
import configparser
import random
import unittest
from datetime import datetime, timezone
from typing import List

from monmon.custom_types.watch_list import WatchListMetrics, WatchList
from monmon.db.db_connector import DbConnector


class TestDB(unittest.IsolatedAsyncioTestCase):
    """Test cases for database methods"""

    async def asyncSetUp(self) -> None:
        cfg = configparser.ConfigParser()
        cfg.read("src/monmon/config.ini")
        db_dsn = cfg["database"].get("test_pg_dsn")
        migrations_dir = "src/monmon/db/migrations"
        self.db_conn = DbConnector(db_dsn, migrations_dir)
        await self.db_conn.apply_migrations()

    async def asyncTearDown(self) -> None:
        await self.db_conn.rollback_migrations()

    async def test_watch_list(self):
        """Testing insert and select a `watch_list`"""
        watch_list: List[WatchList] = [
            {
                "url": "https://example.com/users/1",
                "check_interval_sec": random.randint(5, 301),
                "regexp": "[a-z][A-Z]",
            },
            {
                "url": "https://req-west.dev/users/3",
                "check_interval_sec": random.randint(5, 301),
                "regexp": "abc",
            },
        ]

        saved_wl = await self.db_conn.save_to_watch_list(watch_list)
        if not saved_wl:
            self.fail("failed to save watch list")
        get_wl = await self.db_conn.get_watch_list()

        self.assertCountEqual(saved_wl, get_wl)

    async def test_metrics(self):
        """Testing insert and select a metrics"""
        watch_list: List[WatchList] = [
            {
                "url": "https://example.com/users/1",
                "check_interval_sec": random.randint(5, 301),
                "regexp": "[a-z][A-Z]",
            },
        ]

        saved_wl = await self.db_conn.save_to_watch_list(watch_list)
        if not saved_wl:
            self.fail("failed to save watch list")

        site_id, _, _, _ = next(saved_wl)

        metrics: WatchListMetrics = {
            "site_id": site_id,
            "status_code": 200,
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "response_time": random.randint(30000000, 90000001),
            "content": "test content",
        }
        await self.db_conn.save_metrics(metrics)
        saved_metrics = await self.db_conn.get_metrics(site_id)
        if not saved_metrics:
            self.fail("metrics not saved to database")

        site_id, status_code, timestamp, response_time, content = next(saved_metrics)
        result: WatchListMetrics = {
            "site_id": site_id,
            "status_code": status_code,
            "timestamp": timestamp.isoformat(),
            "response_time": response_time,
            "content": content,
        }
        self.assertEqual(metrics, result)
