"""Schema validators"""
from typing import List, Tuple

import validators


async def is_watch_list_valid(request: List[dict]) -> Tuple[str, bool]:
    """With this module, you can determine if a request is a valid WatchList"""

    if len(request) == 0:
        return "empty request", False

    for req in request:
        url: str = req["url"]
        regexp: str = req["regexp"]
        check_interval_sec: int = req["check_interval_sec"]

        if not validators.url(url):
            return "invalid url", False
        if not validators.length(regexp, 1):
            return "empty regexp", False
        if not validators.between(check_interval_sec, 5, 300):
            return "check_interval_sec must be between 5 and 300", False
    return "ok", True
