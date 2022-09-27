import websockets as ws
import json



class WebSocket():
    websocket = None

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
                await self.send_boot_notification()
        except Exception as e:
            print("fail")
            print(str(e))


    async def send_boot_notification(self):
        """
        I'm trying to send a message to the server, but I'm getting an error
        """
        print("IM BOOT")
        msg = [2, "0jdsEnnyo2kpCP8FLfHlNpbvQXosR5ZNlh8v", "BootNotification", {
            "chargePointVendor": "AVT-Company",
            "chargePointModel": "AVT-Express",
            "chargePointSerialNumber": "avt.001.13.1",
            "chargeBoxSerialNumber": "avt.001.13.1.01",
            "firmwareVersion": "0.9.87",
            "iccid": "",
            "imsi": "",
            "meterType": "AVT NQC-ACDC",
            "meterSerialNumber": "avt.001.13.1.01"}]
        msg_send = json.dumps(msg)
        await self.websocket.send(msg_send)

    async def listen_for_response(self):
        try:
            json_formatted_message = await self.websocket.recv()
            message = json.loads(json_formatted_message)
            print(message)
        except Exception as e:
            print(str(e))
        
            
