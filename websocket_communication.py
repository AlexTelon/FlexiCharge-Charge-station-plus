from asyncio import wait_for
import asyncio
from multiprocessing.connection import wait
import websockets as ws
import json

from ocpp_messages import OCPPMessages



class WebSocket():

    def __init__(self):
        try:
            print("ws_init")
            self.webSocket = None

        except Exception as e:
            self.webSocket = None
            print("ws_init_failed")
            print(str(e))


    async def connect(self):
        try:
            async with ws.connect(
            'ws://18.202.253.30:1337/testnumber13',
            subprotocols=['ocpp1.6'],
            ping_interval=5,
            timeout = None
        ) as webSocketConnection:
                self.webSocket = webSocketConnection
                print("Successfully connected to WebSocket")
                await self.send_boot_notification()
                return True
        except Exception as e:
            print("fail")
            print(str(e))
            return False

    async def send_message(self, json_formatted_message):
        await self.webSocket.send(json_formatted_message)

    async def send_boot_notification(self):
        """
        I'm trying to send a message to the server, but I'm getting an error
        """
        print("Send boot notificaition: ")
        json_msg = json.dumps(OCPPMessages.boot_notification_conf)
        print(str(json_msg))
        await self.webSocket.send(json_msg)

    async def listen_for_response(self):
        try:
            json_formatted_message = await self.webSocket.recv()
            message = json.loads(json_formatted_message)
            print(message)
        except Exception as e:
            print(str(e))
        




