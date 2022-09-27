import websockets as ws
import json

from websocket_messages import WebSocketMessages as wsm



class WebSocket():
    """
    We have tried to rewrite and fix the websockets but we were left with a burning carwreck.
    It does not work and probably wont ever work.
    Increase this timer for every hour spent trying to fix it and make it work.
    And write your name below to we can remember our fallen comrades
    Hours spent in this shithole: 7 (7 too many)

    Albin Samefors was here
    Axel Björkman was here
    """
    #websocket = None

    def __init__(self):
        self.webSocket = self.connect

    async def connect(self):
        try:
            async with ws.connect(
            'ws://18.202.253.30:1337/testnumber13',
            subprotocols=['ocpp1.6'],
            ping_interval=5,
            timeout = None
        ) as ws:
                self.websocket = ws
                print("success")
                await self.send_message(wsm.get_boot_notification_req())

        except Exception as e:
            print("fail")
            print(str(e))
        

    async def send_message(self, json_formatted_message):
        await self.websocket.send(json_formatted_message)
    

    async def send_status_notification(self):
        """
        It sends a message to the back-end with the status of the charging station.

        :param info: A string that contains information about the status
        """
        #Jag har inte varit inne och ändrat någonting här! Detta är gammal skit
        current_time = datetime.now()
        print(current_time)
        # Can be removed if back-end does want the time-stamp formated
        timestamp = current_time.timestamp()
        # Can be removed if back-end does not want the time-stamp formated
        formated_timestamp = current_time.strftime("%Y-%m-%dT%H:%M:%SZ")

        msg = [2, "0jdsEnnyo2kpCP8FLfHlNpbvQXosR5ZNlh8v", "StatusNotification", {
            "connectorId": self.hardcoded_connector_id,
            "errorCode": self.error_code,
            "info"#: info,  # Optional according to official OCPP-documentation
            "status": self.status,
            "timestamp": timestamp,  # Optional according to official OCPP-documentation
            # Optional according to official OCPP-documentation
            "vendorId": self.hardcoded_vendor_id,
            "vendorErrorCode": "None"  # Optional according to official OCPP-documentation
        }]

        msg_send = json.dumps(msg)
        print("Status notification sent with message: ")
        print(msg)
        await self.my_websocket.send(msg_send)
        self.timestamp_at_last_status_notification = time.perf_counter()

    async def listen_for_response(self):
        while True:
            try:
                json_formatted_message = await self.websocket.recv()
                message = json.loads(json_formatted_message)
                print("Got message:")
                print(message)
                if message[2] == "DataTransfer":
                    await self.send_message(wsm.get_boot_notification_conf)
            except Exception as e:
                print(str(e))
        
            
ws = WebSocket()