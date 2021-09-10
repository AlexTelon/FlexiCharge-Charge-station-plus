import asyncio
from src.centralsystem.centralsystem import CentralSystem, create_websocket_server
from src.httpserver.server import create_http_server

async def main():
    csms = CentralSystem()
    websocket_server = await create_websocket_server(csms)
    http_server = await create_http_server(csms)

    await asyncio.wait([websocket_server.wait_closed(), http_server.start()])


if __name__ == "__main__":
    asyncio.run(main())