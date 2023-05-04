"""This file contains custom types for all modules"""
from typing import TypedDict


class WatchList(TypedDict):
    """Custom type for a monitored site"""

    url: str
    regexp: str
    check_interval_sec: int


class WatchListMetrics(TypedDict):
    """Custom type for metrics of sites"""

    site_id: int
    status_code: int
    timestamp: str
    response_time: int
    content: str | None
