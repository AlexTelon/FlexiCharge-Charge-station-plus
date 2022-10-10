import websockets
import asyncio
import json

from variables.reservation_variables import Reservation
from variables.charger_variables import Charger
from variables.misc_variables import Misc

# variables
reservation = Reservation()
charger = Charger()
misc = Misc()

meter_value_dummy = [["timestamp0", "Value0"], ["timestamp1", "Value1"], [
    "timestamp2", "Value2"]]  # list with the metervalue variable. dummy data

# Client
# Note that idTag is RFID tag hardcoded atm should be changed in the future // Elin and Kevin 2022-09-29
boot_message_request = [2, "0jdsEnnyo2kpCP8FLfHlNpbvQXosR5ZNlh8v",
                        "BootNotification", {
                            "chargePointVendor": "AVT-Company",
                            "chargePointModel": "AVT-Express",
                            "chargePointSerialNumber": "avt.001.13.1",
                            "chargeBoxSerialNumber": "avt.001.13.1.01",
                            "firmwareVersion": "0.9.87",
                            "iccid": "",
                            "imsi": "",
                            "meterType": "AVT NQC-ACDC",
                            "meterSerialNumber": "avt.001.13.1.01"}]

authorize_req = [2, "0jdsEnnyo2kpCP8FLfHlNpbvQXosR5ZNlh8v",
                 "Authorize", {
                    "idTag": "330174510923"
                 }]

data_transfer_conf = [2, "0jdsEnnyo2kpCP8FLfHlNpbvQXosR5ZNlh8v",
                      "DataTransfer", {
                          "status": "Accepted",
                          "data": ""  # optional
                      }]

meter_values_req = [2, "0jdsEnnyo2kpCP8FLfHlNpbvQXosR5ZNlh8v",  # OCPP p.73-74
                    "MeterValues", {
                        "connectorId": "",  # Required. This contains a number >0 designating a connector of the charge point '0' is used to designate the main powermeter
                        "transactionId": "",  # Optional
                        "meterValue": meter_value_dummy  # send list of 3 values with timestamp and value
                    }]

start_transaction_req = [2, "0jdsEnnyo2kpCP8FLfHlNpbvQXosR5ZNlh8v",  # OCPP p.79
                         "StartTransaction",
                         {
                             "idTag": "330174510923",  # RFID tag id
                             "meterStart": misc.meter_value_total,  # Meter value in WH
                             "reservationId": reservation.reservation_id,  # Optional
                             "timestamp": ""  # This contains the date and time on which the transaction is started
                         }]


stop_transation_req = [2,  # OCPP p.81
                       "0jdsEnnyo2kpCP8FLfHlNpbvQXosR5ZNlh8v",
                       "StopTransaction",
                       {
                           "idTag": "330174510923",  # RFID tag id
                           "meterStop": charger.charging_Wh,  # send Wh at stop transaction
                           "timestamp": "",  # Date and time for stop transaction
                           "transactionId": "",
                           "transactionData": ""  # optional, contains transaction details e.g KWh / cost ... etc
                       }]

# Server
boot_message_response = [3, '0jdsEnnyo2kpCP8FLfHlNpbvQXosR5ZNlh8v', 'BootNotification', {
    'status': 'Accepted',
    'currentTime': 1663966665,
    'interval': 86400}]

data_transfer_req = [2, '100009DataTransfer1664971239072', 'DataTransfer', {
    'vendorId': 'com.flexicharge', 'messageId': 'BootData', 'data': '{"chargerId":100009,"chargingPrice":"7500.00"}'}]

start_remote_transaction_request = [2,
                                    "0jdsEnnyo2kpCP8FLfHlNpbvQXosR5ZNlh8v",
                                    "RemoteStartTransaction",
                                    {
                                        "idTag": "1"
                                    }]
stop_remote_transation_request = [3,
                                  "0jdsEnnyo2kpCP8FLfHlNpbvQXosR5ZNlh8v",
                                  "RemoteStopTransaction",
                                  {
                                      "status": "Accepted"
                                  }]

start_transaction_conf = [3,  "0jdsEnnyo2kpCP8FLfHlNpbvQXosR5ZNlh8v",  # OCPP p.80
                          "StartTransaction", {
                              "status": "Accepted",
                              "transactionId": ""  # This contains the transaction id supplied by the Central System
                          }]

stop_transaction_conf = [3, "0jdsEnnyo2kpCP8FLfHlNpbvQXosR5ZNlh8v",
                         "StopTransaction",
                         {
                             "idTagInfo": ""  # Optional, Info about auth status
                         }]

meter_values_conf = [3, "0jdsEnnyo2kpCP8FLfHlNpbvQXosR5ZNlh8v",
                     "MeterValues",
                     {
                     }]

authorize_conf = [3, "0jdsEnnyo2kpCP8FLfHlNpbvQXosR5ZNlh8v",
                     "Authorize",
                     {
                         "idTagInfo": ""  # Optional, info about auth status
                     }]


async def ocpp_server(websocket):
    async for message in websocket:
        print(message)
        await websocket.send(json.dumps(boot_message_response))
        print(boot_message_response)
        await websocket.send(json.dumps(data_transfer_req))
        await websocket.send(json.dumps(start_remote_transaction_request))

start_server = websockets.serve(ocpp_server, "127.0.0.1", 60003)

asyncio.get_event_loop().run_until_complete(start_server)
asyncio.get_event_loop().run_forever()
