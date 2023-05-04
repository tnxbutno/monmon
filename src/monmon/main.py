"""Module where all starts"""
import asyncio
import configparser
import logging
import signal

import structlog

from monmon.requester.client import HttpClient
from monmon.watchdog.watcher import Watcher
from monmon.web_server.server import WebServer
from monmon.db.db_connector import DbConnector


async def main():
    """Parse the config and starts all the services"""
    cfg = configparser.ConfigParser()
    cfg.read("config.ini")
    web_host = cfg["web_server"].get("host", "localhost")
    web_port = cfg["web_server"].getint("port", 9080)
    db_dsn = cfg["database"].get(
        "pg_dsn", "postgres://postgres:postgres@localhost:5432/defaultdb?sslmode=false"
    )
    db_migrations_dir = cfg["database"].get("migrations_dir", "db/migrations")
    http_timeout_sec = cfg["http"].getint("timeout_sec", 60)
    log_level = cfg["logger"].get("level", "INFO").upper()

    log = logging.getLogger("main_logger")
    stream_handler = logging.StreamHandler()
    log.setLevel(log_level)
    log.addHandler(stream_handler)
    structlog.configure(
        processors=[
            structlog.stdlib.filter_by_level,
            structlog.processors.TimeStamper(fmt="iso", utc=True),
            structlog.stdlib.PositionalArgumentsFormatter(),
            structlog.stdlib.add_log_level,
            structlog.processors.dict_tracebacks,
            structlog.processors.UnicodeDecoder(),
            structlog.processors.JSONRenderer(),
        ],
        logger_factory=structlog.stdlib.LoggerFactory(),
        cache_logger_on_first_use=True,
    )

    db_conn = DbConnector(db_dsn, db_migrations_dir)
    await db_conn.apply_migrations()

    http_client = HttpClient(http_timeout_sec)
    watcher = Watcher(http_client, db_conn)

    handler = WebServer(web_host, web_port, watcher, db_conn)
    await handler.start()

    watch_list = await db_conn.get_watch_list()
    if watch_list:
        await watcher.add_to_monitoring(watch_list)


async def shutdown(a_loop):
    """Handles graceful shutdown"""
    tasks = [t for t in asyncio.all_tasks() if t is not asyncio.current_task()]

    for task in tasks:
        task.cancel()

    await asyncio.gather(*tasks, return_exceptions=True)
    a_loop.stop()


if __name__ == "__main__":
    loop = asyncio.new_event_loop()
    signals = (signal.SIGHUP, signal.SIGTERM, signal.SIGINT)
    for s in signals:
        loop.add_signal_handler(s, lambda s=s: asyncio.create_task(shutdown(loop)))
    try:
        loop.run_until_complete(main())
        loop.run_forever()
    finally:
        loop.close()
