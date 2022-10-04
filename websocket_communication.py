from asyncio import wait_for
import asyncio
import datetime
import time
from multiprocessing.connection import wait
import webbrowser
from config import Configurations as Config
import websockets as ws
import json
from StateHandler import States
from variables.charger_variables import Charger
from variables.misc_variables import Misc
from variables.reservation_variables import Reservation

from ocpp_messages import OCPPMessages

"""
We have tried to rewrite and fix the websockets but we were left with a burning carwreck.
It does not work and probably wont ever work.
Increase this timer for every hour spent trying to fix it and make it work.
And write your name below to we can remember our fallen comrades
Hours spent in this shithole: 23 (23 too many)

Albin Samefors was here
Axel Björkman was here
Felix Sundman was here
"""


class WebSocket():
    # Get variables
    #charger = None #Should not be here!!
    #misc = None
    #reservation = None

    def __init__(self):
        try:
            print("ws_init")
            self.webSocket = None

        except Exception as e:
            self.webSocket = None
            print("ws_init_failed")
            print(str(e))

    def get_status(self):
        return Misc.status

    async def connect(self):
        """
        It tries to connect to a websocket, if it succeeds it sends a boot notification request.
        :return: The return value is a coroutine object.
        """
        try:
            async with ws.connect(
                Config().getWebSocketAddress(),
                subprotocols= Config().getProtocol(),
                ping_interval= Config().getWebSocketPingInterval(),
                timeout= Config().getWebSocketTimeout()
            ) as webSocketConnection:
                self.webSocket = webSocketConnection
                print("Successfully connected to WebSocket")
                await self.send_boot_notification_req()
                return True
        except Exception as e:
            print("connect failed")
            print(str(e))
            return False

    async def send_message(self, json_formatted_message):
        """
        It sends a message to the websocket

        :param json_formatted_message: The message you want to send to the server
        """
        await self.webSocket.send(json_formatted_message)

    async def send_status_notification(self):
        """
        It sends a message to the back-end with the status of the charging station.

        :param info: A string that contains information about the status
        """
        print("Send STATUS notificaition: ")
        json_msg = json.dumps(OCPPMessages.boot_notification_conf)
        print(str(json_msg))
        await self.send_message(json_msg)

    async def listen_for_response(self):
        """
        It listens for a response from the server and prints it out
        """
        try:
            json_formatted_message = await self.webSocket.recv()
            message = json.loads(json_formatted_message)
            print(message)
            return message
        except Exception as e:
            print(str(e))

    async def get_message(self,charger_variables,misc_variables,reservation_variables):
        """
        It checks for a message from the server, if it gets one, it checks the message type and calls
        the appropriate function.
        """
        # for i in range(3):
        while True: #why while true??
            try:
                #self.charger = charger_variables
                #self.misc = misc_variables
                #self.reservation = reservation_variables
                websocket_timeout = 0.5  # Timeout in seconds
                json_formatted_message = await asyncio.wait_for(self.webSocket.recv(), websocket_timeout)
                # async for msg in self.my_websocket: #Takes latest message
                print("get_message")
                message = json.loads(json_formatted_message)
                print(message)

                if message[2] == "ReserveNow":
                    await asyncio.gather(self.reserve_now(message))
                elif message[2] == "BootNotification":
                    message_str = str(message[3]["status"])
                    if message_str == "Accepted":
                        confirm = await asyncio.gather(self.listen_for_response())
                        if confirm == "sent 1000 (OK); then received 1000 (OK)":
                            return States.S_AVAILABLE
                        pass
                    else:
                        Misc.status = "Faulted"
                        await asyncio.gather(self.send_status_notification())
                        # state.set_state(States.S_NOTAVAILABLE)
                        return States.S_NOTAVAILABLE
                elif message[2] == "RemoteStartTransaction":
                    return await asyncio.gather(self.remote_start_transaction(message))
                elif message[2] == "RemoteStopTransaction":
                    return await asyncio.gather(self.remote_stop_transaction(message))
                elif message[2] == "DataTransfer":
                    Charger.charger_id = json.loads(message[5]["chargerId"])
                    return await asyncio.gather(self.data_transfer_response(message))

                elif message[2] == "StartTransaction":
                    pass
                    self.transaction_id = 347
                elif message[2] == "NotImplemented":
                    print(message[3])
            except Exception as e:
                print("Get_message ERROR:")
                print(e)
                break

    async def update_charger_data(self):
        return Misc.status, Charger.charger_id

    async def get_reservation_info(self):
        return Reservation.is_reserved, Misc.status, Reservation.reservation_id_tag, Reservation.reservation_id, Reservation.reserved_connector, Reservation.reserve_now_timer

    async def data_transfer_request(self, message_id, message_data):
        """
        The function takes in a message_id and message_data, and then sends a message to the websocket

        :param message_id: The message id of the message you want to respond to
        :param message_data: This is the data that you want to send to the EVSE
        """
        s: str = "{}{}{}{}{}{}{}".format("{\"transactionID\":", self.transaction_id,
                                         ",\"latestMeterValue\":", message_data, ",\"CurrentChargePercentage\":", message_data, "}")
        print(s)
        # msg_id = self.charger_id + "DataTransfer" +

        msg = [2, "0jdsEnnyo2kpCP8FLfHlNpbvQXosR5ZNlh8v", "DataTransfer", {
            "vendorId": "com.flexicharge",
            "messageId": "BootData",
            "data": s
        }]
        msg_send = json.dumps(msg)
        await self.send_message(msg_send)

    # Does not work as of now
    async def data_transfer_response(self, message):
        status = "Rejected"
        if message[3]["vendorId"] == "com.flexicharge":
            if message[3]["messageId"] == "BootData":
                parsed_data = json.loads(message[3]["data"])
                Charger.charger_id = parsed_data["chargerId"]
                print("Charger ID is set to: " + str(Charger.charger_id))
                status = "Accepted"
            else:
                status = "UnknownMessageId"
                print("UnknownMessageId")
        else:
            status = "UnknownVendorId"
            print("UnknownVendorId")
        # Send a conf
        conf_msg = [3,
                    message[1],
                    "DataTransfer",
                    {"status": status}]
        # MIGHT BE PROBLEMS HERE
        conf_send = json.dumps(conf_msg)
        print("Sending confirmation: " + conf_send)
        await self.send_message(conf_send)


####################Start/Stop Transaction####################
#                 Page 39 in the OCPP Manual                 #

    async def start_transaction(self, is_remote):
        """
        If the charging is remote, then the charging has already started in the remote_start_transaction
        function. Notify the server here

        :param is_remote: True if the charging was started remotely, False if it was started locally
        """
        current_time = datetime.now()
        timestamp = current_time.timestamp()

        if is_remote == True:
            # If remote then charging have started in remote_start_transaction. Notify server here.
            msg = [2, "0jdsEnnyo2kpCP8FLfHlNpbvQXosR5ZNlh8v", "StartTransaction", {
                "connectorId": Charger.charging_connector,
                "id_tag": Charger.charging_id_tag,
                "meterStart": Misc.meter_value_total,
                "timestamp": timestamp,
                "reservationId": Reservation.reservation_id,
            }]

            self.hard_reset_reservation()
            msg_send = json.dumps(msg)
            await self.send_message(msg_send)
        else:  # No reservation
            self.start_charging(self.hardcoded_connector_id,
                                self.hardcoded_id_tag)

            msg = [2, "0jdsEnnyo2kpCP8FLfHlNpbvQXosR5ZNlh8v", "StartTransaction", {
                "connectorId": self.charging_connector,
                "id_tag": self.charging_id_tag,
                "meterStart": self.meter_value_total,
                "timestamp": timestamp,
                "reservationId": None,  # If here, no reservation was made
            }]

            msg_send = json.dumps(msg)
            await self.send_message(msg_send)
        pass

    async def stop_transaction(self, is_remote):
        """
        It stops the transaction and sends a message to the server.

        :param is_remote: Boolean
        """
        current_time = datetime.now()
        timestamp = current_time.timestamp()
        Misc.status = "Available"
        await asyncio.gather(self.send_status_notification(None))
        if is_remote == True:
            msg = [2, "0jdsEnnyo2kpCP8FLfHlNpbvQXosR5ZNlh8v", "StopTransaction", {
                "idTag": Charger.charging_id_tag,
                "meterStop": Misc.meter_value_total,
                "timestamp": timestamp,
                "transactionId": self.transaction_id,
                "reason": "Remote",
                "transactionData": None  # [
                # {
                # Can place timestamp here. (Optional)
                # },
                # Can place meterValues here. (Optional)
                # ]
            }]
            msg_send = json.dumps(msg)
            await self.send_message(msg_send)
            self.hard_reset_charging()
        else:
            msg = [2, "0jdsEnnyo2kpCP8FLfHlNpbvQXosR5ZNlh8v", "StopTransaction", {
                "idTag": Charger.charging_id_tag,
                "meterStop": Misc.meter_value_total,
                "timestamp": timestamp,
                "transactionId": self.transaction_id,
                "reason": "Remote",
                "transactionData": None  # [
                # {
                # Can place timestamp here. (Optional)
                # },
                # Can place meterValues here. (Optional)
                # ]
            }]
            msg_send = json.dumps(msg)
            await self.send_message(msg_send)
            self.hard_reset_charging()

        response = await self.my_websocket.recv()
        print(json.loads(response))

    async def remote_stop_transaction(self, message):
        """
        If the charging is true and the local transaction id is equal to the transaction id, then print
        "Remote stop charging" and send a message to the server.

        :param message: The message received from the server
        """
        local_transaction_id = message[3]["transactionID"]
        # and int(local_transaction_id) == int(self.transaction_id):
        if Charger.is_charging == True:
            print("Remote stop charging")
            msg = [3,
                   # Have to use the unique message id received from server
                   message[1],
                   "RemoteStopTransaction",
                   {"status": "Accepted"}
                   ]
            msg_send = json.dumps(msg)
            await self.send_message(msg_send)
            # Stop transaction and inform server
            await self.stop_transaction(is_remote=True)
        else:
            print("Charging cannot be stopped")
            msg = [3,
                   # Have to use the unique message id received from server
                   message[1],
                   "RemoteStopTransaction",
                   {"status": "Rejected"}
                   ]
            msg_send = json.dumps(msg)
            await self.send_message(msg_send)

    async def remote_start_transaction(self, message):
        """
        If the idTag has a reservation, start charging from the reservation, set the state to charging,
        send a response to the central system, start the transaction, set the status to charging, and
        send a status notification to the central system.

        :param message: [3, "Unique message id", "RemoteStartTransaction", {"idTag": "12345"}]
        """
        if int(message[3]["idTag"]) == self.reservation_id_tag:  # If the idTag has a reservation
            self.start_charging_from_reservation()
            print("Remote transaction started")
            # state.set_state(States.S_CHARGING)
            msg = [3,
                   message[1],  # Unique message id
                   "RemoteStartTransaction",
                   {"status": "Accepted"}
                   ]
            response = json.dumps(msg)
            await self.send_message(response)

            await self.start_transaction(is_remote=True)
            self.status = "Charging"
            # Notify central system that connector is now available
            await self.send_status_notification(None)
            print("Charge should be started")
            return States.S_CHARGING
        else:  # A non reserved tag tries to use the connector
            print("This tag does not have a reservation")
            msg = [3,
                   message[1],  # Unique message id
                   "RemoteStartTransaction",
                   {"status": "Rejected"}
                   ]
            response = json.dumps(msg)
            await self.send_message(response)


##############################################################


    async def reserve_now(self, message):
        local_reservation_id = message[3]["reservationID"]
        local_connector_id = message[3]["connectorID"]
        if Reservation.reservation_id == None or Reservation.reservation_id == local_reservation_id:
            if Reservation.reserved_connector == False and local_connector_id == 0:
                print("Connector zero not allowed")
                msg = [3,
                       # Have to use the unique message id received from server
                       message[1],
                       "ReserveNow",
                       {"status": "Rejected"}
                       ]
                msg_send = json.dumps(msg)
                await self.send_message(msg_send)
                return
            self.hard_reset_reservation()
            Reservation.is_reserved = True
            Misc.status = "Reserved"
            await asyncio.gather(self.send_status_notification(None))
            # state.set_state(States.S_FLEXICHARGEAPP)
            self.resevation.reservation_id_tag = int(message[3]["idTag"])
            self.resevation.reservation_id = message[3]["reservationID"]
            self.resevation.reserved_connector = message[3]["connectorID"]
            timestamp = message[3]["expiryDate"]  # Given in ms since epoch
            reserved_for_s = int(timestamp - int(time.time()))
            # reserved_for_ms/1000)   #Reservation time in seconds
            self.resevation.reserve_now_timer = int(reserved_for_s)
            self.timer_countdown_reservation  # Countdown every second

            msg = [3,
                   # Have to use the unique message id received from server
                   message[1],
                   "ReserveNow",
                   {"status": "Accepted"}
                   ]
            msg_send = json.dumps(msg)
            await self.send_message(msg_send)
            return States.S_FLEXICHARGEAPP
        elif Reservation.reserved_connector == local_connector_id:
            print("Connector occupied")
            msg = [3,
                   # Have to use the unique message id received from server
                   message[1],
                   "ReserveNow",
                   {"status": "Occupied"}
                   ]
            msg_send = json.dumps(msg)
            await self.send_message(msg_send)
        else:
            print("Implement other messages for non accepted reservations")
            msg = [3,
                   # Have to use the unique message id received from server
                   message[1],
                   "ReserveNow",
                   {"status": "Occupied"}
                   ]
            msg_send = json.dumps(msg)
            await self.send_message(msg_send)

    async def send_boot_notification_req(self):
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
        print("Sending boot notification")
        await self.send_message(msg_send)

    async def send_boot_notification_conf(self, message):
        conf_msg = [3,
                    message[1],
                    "DataTransfer",
                    {"status": "Accepted"}]
        conf_send = json.dumps(conf_msg)
        print("Sending confirmation: " + conf_send)
        try:
            await self.send_message(conf_send)
            print("Message went away")
        except Exception as e:
            print(str(e))

    async def start_charging_from_reservation(self):
        pass

    async def hard_reset_charging(self):
        pass

    async def hard_reset_reservation(self):
        pass
