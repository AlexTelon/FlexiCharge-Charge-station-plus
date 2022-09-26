import websockets
import asyncio
import json

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
start_transaction_request = [ 3,
  "0jdsEnnyo2kpCP8FLfHlNpbvQXosR5ZNlh8v",
  "RemoteStartTransaction",
  { 
    "status": "Accepted"
    } ]     
stop_transation_request = [ 3,
  "0jdsEnnyo2kpCP8FLfHlNpbvQXosR5ZNlh8v",
  "RemoteStopTransaction",
  { 
    "status": "Accepted"
    } ]       


async def ocpp_server(websocket):
    async for message in websocket:
        print(message)
        await websocket.send(json.dumps(boot_message_response))
        print(boot_message_response)
        await websocket.send(json.dumps(start_transaction_request))

start_server = websockets.serve(ocpp_server, "127.0.0.1", 60003)

asyncio.get_event_loop().run_until_complete(start_server)
asyncio.get_event_loop().run_forever()
