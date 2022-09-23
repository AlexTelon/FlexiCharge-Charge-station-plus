import websockets
import asyncio

boot_message_response = [3, '0jdsEnnyo2kpCP8FLfHlNpbvQXosR5ZNlh8v', 'BootNotification', {
    'status': 'Accepted',
    'currentTime': 1663966665,
    'interval': 86400}]

boot_message_request = [2, "0jdsEnnyo2kpCP8FLfHlNpbvQXosR5ZNlh8v", "BootNotification", {
    "chargePointVendor": "AVT-Company",
    "chargePointModel": "AVT-Express",
    "chargePointSerialNumber": "avt.001.13.1",
    "chargeBoxSerialNumber": "avt.001.13.1.01",
    "firmwareVersion": "0.9.87",
    "iccid": "",
    "imsi": "",
            "meterType": "AVT NQC-ACDC",
            "meterSerialNumber": "avt.001.13.1.01"}]


async def ocpp_server(websocket, path):
    data = await websocket.recv()
    if data == boot_message_request:
        await websocket.send(boot_message_request)


start_server = websockets.serve(ocpp_server, "127.0.0.1", 60003)

asyncio.get_event_loop().run_until_complete(start_server)
asyncio.get_event_loop().run_forever()
