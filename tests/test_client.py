"""Tests for requester module"""
import unittest
import re

from aiohttp import web

from monmon.requester.client import HttpClient


async def mock_server(_resp):
    """This method initiates the webserver for simulating responses from real websites"""
    return web.Response(
        text="""
                        <!DOCTYPE html>
                        <html>
                        <body>
                        
                        <h1>find me plz</h1>
                        <p>hehehe find me if you can!</p>
                        <p>123</p>
                        <p>12</p>
                        
                        </body>
                        </html>
                    """
    )


class TestClient(unittest.IsolatedAsyncioTestCase):
    """Test cases for client"""

    async def asyncSetUp(self) -> None:
        # Setup server stuff here
        self.app = web.Application()
        self.app.router.add_get("/", mock_server)
        runner = web.AppRunner(self.app)
        await runner.setup()
        self.site = web.TCPSite(runner, port=8000)
        await self.site.start()

        # Setup http client stuff here
        self.http_client = HttpClient(timeout_sec=7)

    async def asyncTearDown(self) -> None:
        await self.http_client.close_session()
        await self.app.cleanup()
        await self.site.stop()

    async def test_regex_matching(self) -> None:
        """This is a test to check how regex matching works"""
        testcases = [
            {
                "site_id": 1,
                "url": "http://localhost:8000/",
                "regexp": re.compile("find me"),
                "expected": "find me\nfind me",
            },
            {
                "site_id": 1,
                "url": "http://localhost:8000/",
                "regexp": re.compile("123"),
                "expected": "123",
            },
            {
                "site_id": 1,
                "url": "http://localhost:8000/",
                "regexp": re.compile("no match"),
                "expected": "",
            },
            {
                "site_id": 1,
                "url": "http://localhost:8000/",
                "regexp": re.compile(""),
                "expected": "",
            },
        ]
        for site in testcases:
            response = await self.http_client.get(
                site["site_id"], site["url"], site["regexp"]
            )
            self.assertEqual(response["content"], site["expected"])

    async def test_responses(self) -> None:
        """This is a test to check the correctness of returned http status codes"""
        testcases = [
            {
                "site_id": 1,
                "url": "http://localhost:8000/",
                "regexp": re.compile("find me"),
                "expected": 200,
            },
            {
                "site_id": 1,
                "url": "http://localhost:8000/404",
                "regexp": re.compile("no match"),
                "expected": 404,
            },
        ]
        for site in testcases:
            response = await self.http_client.get(
                site["site_id"], site["url"], site["regexp"]
            )
            self.assertEqual(response["status_code"], site["expected"])

    async def test_none_return(self) -> None:
        """Testing that None is returned when problems occur."""
        testcases = [
            {
                "site_id": 1,
                "url": "",
                "regexp": re.compile("find me"),
                "expected": None,
            },
        ]
        for site in testcases:
            response = await self.http_client.get(
                site["site_id"], site["url"], site["regexp"]
            )
            self.assertEqual(response, site["expected"])
