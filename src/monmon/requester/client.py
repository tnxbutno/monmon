"""This module abstracts the HTTP library,
 allowing you to use it without having to worry about the specific implementation."""
import http
import re
from datetime import datetime

import time
import aiohttp
import structlog

from monmon.custom_types.watch_list import WatchListMetrics


class HttpClient:
    """This class allows for making HTTP calls and parsing content using regular expressions."""

    def __init__(self, timeout_sec: int = 60) -> None:
        timeout = aiohttp.ClientTimeout(total=timeout_sec)
        self.session = aiohttp.ClientSession(timeout=timeout)
        self.logger = structlog.getLogger("main_logger")

    async def get(
        self, site_id: int, url: str, regexp: re.Pattern
    ) -> WatchListMetrics | None:
        """Get the URL and parse its content with regexp (only if the response is 200)"""
        result: WatchListMetrics = {
            "site_id": -1,
            "status_code": 0,
            "timestamp": "",
            "response_time": -1,
            "content": None,
        }
        start = time.time_ns()
        try:
            async with self.session.get(url, ssl=False) as response:
                result["site_id"] = site_id
                result["status_code"] = response.status
                result["timestamp"] = datetime.now().isoformat()
                result["response_time"] = time.time_ns() - start
                html = await response.text()
                result["content"] = None
                if response.status == http.HTTPStatus.OK:
                    result["content"] = "\n".join(regexp.findall(html)).lstrip("\n")
            if len(result) > 0:
                self.logger.debug(
                    "got this response while monitoring the site",
                    url=url,
                    status_code=result["status_code"],
                )
                return result

            self.logger.debug("empty response for the site", site_id=site_id, url=url)
            return None
        except aiohttp.client.ClientError as error:
            self.logger.error("cannot get the site content", error=error)
            return None

    async def close_session(self) -> None:
        """This method closes the HTTP session."""
        await self.session.close()
