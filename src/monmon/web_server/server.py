"""This module provides a web server application."""
import http
from typing import List

import structlog
from aiohttp import web, ClientError

from monmon.custom_types.watch_list import WatchList
from monmon.db.db_connector import DbConnector
from monmon.db.pg.exceptions import QueryException
from monmon.schemas.watch_list import is_watch_list_valid
from monmon.watchdog.watcher import Watcher


class WebServer:
    """In this class, there is a methods that deals with a web server.
    Its purpose is to manage user requests and to initiate and operate a web server.
    """

    def __init__(
        self, host: str, port: int, watcher: Watcher, db_conn: DbConnector
    ) -> None:
        self.host = host
        self.port = port
        self.watcher = watcher
        self.db_conn = db_conn
        self.logger = structlog.getLogger("main_logger")

    async def add_to_monitoring_handler(self, request: web.BaseRequest) -> web.Response:
        """This method will analyze the requests made by the user,
        store the associated URLs in the database,
        and include them in the monitoring process."""
        if not request.body_exists:
            return web.Response(
                status=http.HTTPStatus.BAD_REQUEST, text="empty body request"
            )
        req = await request.json()
        msg, is_valid = await is_watch_list_valid(req)
        if not is_valid:
            return web.Response(status=http.HTTPStatus.BAD_REQUEST, text=msg)
        watch_list: List[WatchList] = req
        try:
            saved_wl = await self.db_conn.save_to_watch_list(watch_list)
            if saved_wl:
                await self.watcher.add_to_monitoring(saved_wl)
        except (QueryException, ClientError):
            return web.Response(
                status=http.HTTPStatus.INTERNAL_SERVER_ERROR, text="URLs cannot be add"
            )
        return web.Response(text="the URL added to the monitoring")

    async def start(self) -> None:
        """This method is responsible for registering routes and initiating a web server."""
        app = web.Application()
        app.add_routes(
            [
                web.post("/", self.add_to_monitoring_handler),
            ]
        )

        runner = web.AppRunner(app)
        await runner.setup()
        site = web.TCPSite(runner, host=self.host, port=self.port)
        await site.start()
        self.logger.info("the web server started", host=self.host, port=self.port)
