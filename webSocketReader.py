from platform import machine
import websockets
import asyncio
from config import Configurations
from state_machine import Chargepoint
import json


class WebSocketReader():

    async def connectToWebSocket(self):
        try:
            webSocket = websockets.connect(
                self.webSocketAddress, Configurations.getProtocol)

            return webSocket
        except:
            pass

    async def testSendReceive(self):
        async with websockets.connect(
                self.webSocketAddress) as webSocket:
            await webSocket.send(json.dumps([2,
                                             "WRITE SOMTHING LONG THAT SHOULD ACT AS A UNIQUIE ID HERE",
                                             "StatusNotification",
                                             {
                                                 "errorCode": "NoError",
                                                 "status": "Available"
                                             }]))
            await webSocket.recv()

    def __init__(self) -> None:
        self.webSocketAddress = Configurations.getWebSocketAddress()
        self.testSendReceive()
        pass

    async def getRequest(self):
        try:
            # Wait for request from the server with the specific WebSocket adress
            json_request = asyncio.wait_for(self.webSocketAddress.recv(), 0.1)
            print("Check for message")
            # Converts json request to string
            string_request = json.loads(json_request)
            print(string_request)
        except:
            pass
