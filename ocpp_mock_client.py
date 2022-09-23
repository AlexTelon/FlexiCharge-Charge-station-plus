import websockets
import asyncio

async def ocpp_server(websocket, path):
    async for message in websocket:
        await websocket.send(message)
    
start_server = websockets.serve(ocpp_server, "127.0.0.1", 60003)

asyncio.get_event_loop().run_until_complete(start_server)
asyncio.get_event_loop().run_forever()
