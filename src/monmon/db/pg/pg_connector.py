"""Module abstract database connection, so you don't care what driver you use"""
from typing import Iterator, Any

import psycopg2 as pg
import structlog
from psycopg2 import OperationalError

from monmon.db.pg.exceptions import OpenConnectionException, QueryException


class PgConnector:
    """
    This class functions as a PostgreSQL connector,
    enabling users to establish a connection and perform
    database-related tasks.
    The connection is automatically terminated upon the class's destruction.

    Attributes
    ---------
    logger:
        an instance of main logger
    conn:
        database connection
    """

    def __init__(self, dsn: str) -> None:
        """
        :param dsn: str
            credentials for database connection
        """
        self.logger = structlog.getLogger("main_logger")

        try:
            self.conn = pg.connect(dsn)
        except OperationalError as error:
            self.logger.error("cannot connect to a postgres", error=error)
            raise OpenConnectionException(error) from error

    async def query(self, query: str, params=None) -> Iterator[Any] | None:
        """Execute query with its params.

        :param query: str
            query that must be executed
        :param params: dict
            params for current query
        :return: None
        """
        with self.conn:
            with self.conn.cursor() as curr:
                try:
                    curr.execute(query, params)
                except pg.Error as error:
                    self.logger.error("error while executing a query", error=error)
                    raise QueryException(error) from error
                if curr.description:
                    return iter(curr.fetchall())
                return None

    def __del__(self) -> None:
        try:
            self.conn.close()
        except OperationalError as error:
            self.logger.error("cannot close connection to a postgres", error=error)
