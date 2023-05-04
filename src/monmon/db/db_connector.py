"""This module enables abstract database connection, which means
you don't need to worry about which DB you are using."""
from datetime import datetime
from typing import Iterator, List

import structlog
from yoyo.exceptions import BadMigration, MigrationConflict, LockTimeout
from yoyo import read_migrations
from yoyo import get_backend

from monmon.custom_types.watch_list import WatchList, WatchListMetrics
from monmon.db.pg.exceptions import QueryException
from monmon.db.pg.pg_connector import PgConnector


class DbConnector(PgConnector):
    """With this class, you can apply and roll back migrations
    and save and retrieve data from the database using provided methods."""

    def __init__(self, dsn: str, migration_dir: str) -> None:
        super().__init__(dsn)
        self.migrations = read_migrations(migration_dir)
        self.migrations_conn = get_backend(dsn)
        self.logger = structlog.getLogger("main_logger")
        self.logger.info("connected to database")

    async def apply_migrations(self) -> None:
        """Apply SQL migrations to a database"""
        try:
            with self.migrations_conn.lock():
                self.migrations_conn.apply_migrations(
                    self.migrations_conn.to_apply(self.migrations)
                )
        except (BadMigration, MigrationConflict, LockTimeout) as error:
            self.logger.error(
                "got an error while running database migrations: trying to rollback",
                error=error,
            )
            self.migrations_conn.unlock()
            await self.rollback_migrations()
            raise error

    async def rollback_migrations(self) -> None:
        """Rollback SQL migrations from a database"""
        try:
            with self.migrations_conn.lock():
                self.migrations_conn.rollback_migrations(
                    self.migrations_conn.to_rollback(self.migrations)
                )
        except (BadMigration, MigrationConflict, LockTimeout) as error:
            self.logger.error(
                "got an error during rollback database migrations", error=error
            )
            raise error

    async def save_metrics(self, metrics: WatchListMetrics) -> None:
        """
        This method saves metrics to a database.
        :param metrics: what we want to save
        :return:
        """
        site_id = metrics["site_id"]
        timestamp = metrics["timestamp"]
        response_time = metrics["response_time"]
        status_code = metrics["status_code"]
        content = metrics["content"]
        query = (
            "insert into metrics (site_id, timestamp, response_time, status_code, content) values "
            "(%(site_id)s, %(timestamp)s, %(response_time)s, %(status_code)s, %(content)s);"
        )
        try:
            await self.query(
                query,
                {
                    "site_id": site_id,
                    "timestamp": timestamp,
                    "response_time": response_time,
                    "status_code": status_code,
                    "content": content,
                },
            )
        except QueryException:
            return None

    async def get_metrics(
        self, site_id: int
    ) -> Iterator[tuple[int, int, datetime, int, str]] | None:
        """
        This method gets metrics from a database.
        :param site_id: metrics for given site
        :return:
        """
        query = (
            "select site_id, status_code, timestamp, response_time, content from "
            "metrics where site_id = %(site_id)s"
        )
        try:
            return await self.query(
                query,
                {
                    "site_id": site_id,
                },
            )
        except QueryException:
            return None

    async def get_watch_list(self) -> Iterator[tuple[int, str, str, int]] | None:
        """
        This method retrieves all site settings that require monitoring.
        :return: List[str]
            list of all sites settings
        """
        self.logger.debug("get urls for monitoring from database")
        try:
            return await self.query(
                "select site_id, url, regexp, check_interval_sec from watch_list;"
            )
        except QueryException:
            return None

    async def save_to_watch_list(
        self, watch_list: List[WatchList]
    ) -> Iterator[tuple[int, str, str, int]] | None:
        """
        This method saves preferences for a site.

        :param watch_list: is a list of objects with fields:
            url:  address
            regexp: regexp with witch we should match content on a site
            check_interval_sec: how often check a site content
        :return:
        """
        query = "insert into watch_list (url, regexp, check_interval_sec) values "
        for site in watch_list:
            url, regexp, check_interval_sec = (
                site["url"],
                site["regexp"],
                site["check_interval_sec"],
            )
            query = query + f"('{url}', '{regexp}', {check_interval_sec}), "

        query = query.rstrip(", ") + " returning *;"
        try:
            return await self.query(query)
        except QueryException as error:
            self.logger.error(
                "got an error while saving URLs to a watch list", error=error
            )
            raise error
