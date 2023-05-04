"""Tests for schemas validations"""
import unittest

from monmon.schemas.watch_list import is_watch_list_valid


class TestValidators(unittest.IsolatedAsyncioTestCase):
    """Test cases for validation module"""

    async def test_watch_list_valid(self) -> None:
        """Test checks valid requests for `watch_list`"""
        testcases = [
            [
                {
                    "url": "https://example.com/brrr.html",
                    "regexp": "^[a-z]*",
                    "check_interval_sec": 30,
                }
            ],
            [
                {
                    "url": "https://example.com/brrr.html",
                    "regexp": "^[a-z]*",
                    "check_interval_sec": 5,
                }
            ],
            [
                {
                    "url": "https://example.com/brrr.html",
                    "regexp": "^[a-z]*",
                    "check_interval_sec": 300,
                }
            ],
        ]
        for req in testcases:
            _, is_valid = await is_watch_list_valid(req)
            self.assertEqual(is_valid, True)

    async def test_watch_list_invalid(self) -> None:
        """Test check invalid requests for `watch_list`"""
        testcases = [
            [
                {
                    "url": "https://example.com/brrr.html",
                    "regexp": "^[a-z]*",
                    "check_interval_sec": 4,
                }
            ],
            [
                {
                    "url": "https://example.com/brrr.html",
                    "regexp": "^[a-z]*",
                    "check_interval_sec": 301,
                }
            ],
            [
                {
                    "url": "https://example.com/brrr.html",
                    "regexp": "",
                    "check_interval_sec": 30,
                }
            ],
            [{"url": "", "regexp": "^[a-z]*", "check_interval_sec": 301}],
            [
                {
                    "url": "wedlkm@gmai.com",
                    "regexp": "^[a-z]*",
                    "check_interval_sec": 301,
                }
            ],
            [],
        ]
        for req in testcases:
            _, is_valid = await is_watch_list_valid(req)
            self.assertEqual(is_valid, False)
