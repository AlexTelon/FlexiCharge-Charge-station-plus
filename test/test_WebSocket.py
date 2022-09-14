import asyncio
from sqlite3 import connect
import websockets


class TestWebSocket():
    def test_url(url, data=""):
        async def inner():
            async with websockets.connect(url) as websocket:
                await websocket.send(data)
        return asyncio.get_event_loop().run_until_complete(inner())

    test_url("ws://18.202.253.30:1337/testnumber13")
