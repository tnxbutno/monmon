"""The module monitors websites and records their metrics"""
import asyncio
import re
from typing import Iterator
import structlog

from monmon.db.db_connector import DbConnector
from monmon.requester.client import HttpClient


class Watcher:
    """This class allows you to add new websites for monitoring, tracking, and saving metrics to a database"""

    def __init__(self, http_client: HttpClient, db_conn: DbConnector) -> None:
        self.http_client = http_client
        self.db_conn = db_conn
        self.logger = structlog.getLogger("main_logger")

    async def add_to_monitoring(
        self, watch_list: Iterator[tuple[int, str, str, int]]
    ) -> None:
        """This method starts monitoring a specific list of URLs by periodically
        sending GET requests and storing the results in a database.
         watch_list:
            site_id, url, regexp, check_interval_sec
        """
        loop = asyncio.get_running_loop()
        loop.create_task(self._ticker(watch_list))

    async def _ticker(self, watch_list: Iterator[tuple[int, str, str, int]]) -> None:
        started_tasks = [asyncio.create_task(self._tick(site)) for site in watch_list]
        for task in started_tasks:
            await task

    async def _tick(self, site: tuple[int, str, str, int]) -> None:
        """This method performs HTTP GET requests and stores data on performance metrics."""
        site_id, url, regexp, check_interval_sec = site
        compiled_regexp: re.Pattern = re.compile(regexp)

        self.logger.info(
            "the site added to a monitoring",
            site_id=site_id,
            url=url,
            time_interval=check_interval_sec,
        )
        while True:
            metrics = await self.http_client.get(site_id, url, compiled_regexp)
            if metrics:
                await self.db_conn.save_metrics(metrics)
            await asyncio.sleep(check_interval_sec)
