from asyncio import wait_for
import asyncio
import datetime
from multiprocessing.connection import wait
import webbrowser
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
Hours spent in this shithole: 9 (9 too many)

Albin Samefors was here
Axel Björkman was here
"""

class WebSocket():
    # Get variables
    charger = Charger()
    misc = Misc()
    reservation = Reservation()

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
                timeout=None
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
        try:
            json_formatted_message = await self.webSocket.recv()
            message = json.loads(json_formatted_message)
            print(message)
        except Exception as e:
            print(str(e))

    async def get_message(self):
        """
        It checks for a message from the server, if it gets one, it checks the message type and calls
        the appropriate function.
        """
        for i in range(3):
            try:
                websocket_timeout = 0.5  # Timeout in seconds
                json_formatted_message = await asyncio.wait_for(self.webSocket.recv(), websocket_timeout)
                # async for msg in self.my_websocket: #Takes latest message
                print("Check for message")
                message = json.loads(json_formatted_message)
                print(message)

                if message[2] == "ReserveNow":
                    await asyncio.gather(self.reserve_now(message))
                elif message[2] == "BootNotification":
                    message_str = str(message[3]["status"])
                    if message_str == "Accepted":
                        await self.recive_data_transfer(message)
                        # self.status = "Available"
                        # state.set_state(States.S_AVAILABLE)
                        # return States,S_AVIl
                        # Status notification should be sent after a boot
                        # await asyncio.gather(self.send_status_notification())
                        return States.S_AVAILABLE
                    else:
                        self.status = "Faulted"
                        await asyncio.gather(self.send_status_notification())
                        # state.set_state(States.S_NOTAVAILABLE)
                        return States.S_NOTAVAILABLE
                elif message[2] == "RemoteStartTransaction":
                    return await asyncio.gather(self.remote_start_transaction(message))
                elif message[2] == "RemoteStopTransaction":
                    return await asyncio.gather(self.remote_stop_transaction(message))
                elif message[2] == "DataTransfer":
                    return await asyncio.gather(self.recive_data_transfer(message))
                elif message[2] == "StartTransaction":
                    pass
                    self.transaction_id = 347
                elif message[2] == "NotImplemented":
                    print(message[3])
            except:
                pass

    async def update_charger_data(self):
        return self.misc.status, self.charger.charger_id

    async def get_reservation_info(self):
        return self.reservation.is_reserved, self.misc.status, self.reservation.reservation_id_tag, self.reservation.reservation_id, self.reservation.reserved_connector, self.reservation.reserve_now_timer

    async def data_transfer_request(self, message_id, message_data):
        """
        The function takes in a message_id and message_data, and then sends a message to the websocket

        :param message_id: The message id of the message you want to respond to
        :param message_data: This is the data that you want to send to the EVSE
        """
        s: str = "{}{}{}{}{}{}{}".format("{\"transactionID\":", self.transaction_id,
                                         ",\"latestMeterValue\":", message_data, ",\"CurrentChargePercentage\":", message_data, "}")
        print(s)

        msg = [2, "<unique msg id>", "DataTransfer", {
            "vendorId": "<Put VendorId here>",
            "messageId": message_id,
            "data": s
        }]
        msg_send = json.dumps(msg)
        await self.my_websocket.send(msg_send)

    async def data_transfer_response(self, message):
        status = "Rejected"
        if message[3]["vendorId"] == "<Put VendorId here>":
            if message[3]["messageId"] == "BootData":
                parsed_data = json.loads(message[3]["data"])
                self.charger.charger_id = parsed_data["chargerId"]
                print("Charger ID is set to: " + str(self.charger.charger_id))
                status = "Accepted"
            else:
                status = "UnknownMessageId"
        else:
            status = "UnknownVendorId"
        # Send a conf
        conf_msg = [3,
                    message[1],
                    "DataTransfer",
                    {"status": status}]
        # MIGHT BE PROBLEMS HERE
        conf_send = json.dumps(conf_msg)
        print("Sending confirmation: " + conf_send)
        await self.my_websocket.send(conf_send)


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
                "connectorId": self.charging_connector,
                "id_tag": self.charging_id_tag,
                "meterStart": self.meter_value_total,
                "timestamp": timestamp,
                "reservationId": self.reservation_id,
            }]

            self.hard_reset_reservation()
            msg_send = json.dumps(msg)
            await self.webSocket.send(msg_send)
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
            await self.webSocket.send(msg_send)
        pass

    async def stop_transaction(self, is_remote):
        """
        It stops the transaction and sends a message to the server.

        :param is_remote: Boolean
        """
        current_time = datetime.now()
        timestamp = current_time.timestamp()
        self.misc.status = "Available"
        await asyncio.gather(self.send_status_notification(None))
        if is_remote == True:
            msg = [2, "<unique msg id>", "StopTransaction", {
                "idTag": self.charger.charging_id_tag,
                "meterStop": self.misc.meter_value_total,
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
            await self.webSocket.send(msg_send)
            self.hard_reset_charging()
        else:
            msg = [2, "<unique msg id>", "StopTransaction", {
                "idTag": self.charger.charging_id_tag,
                "meterStop": self.misc.meter_value_total,
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
            await self.webSocket.send(msg_send)
            self.hard_reset_charging()

        response = await self.webSocket.recv()
        print(json.loads(response))

    
    async def remote_stop_transaction(self, message):
            """
            If the charging is true and the local transaction id is equal to the transaction id, then print
            "Remote stop charging" and send a message to the server.

            :param message: The message received from the server
            """
            local_transaction_id = message[3]["transactionID"]
            # and int(local_transaction_id) == int(self.transaction_id):
            if self.is_charging == True:
                print("Remote stop charging")
                msg = [3,
                    # Have to use the unique message id received from server
                    message[1],
                    "RemoteStopTransaction",
                    {"status": "Accepted"}
                    ]
                msg_send = json.dumps(msg)
                await self.my_websocket.send(msg_send)
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
                await self.my_websocket.send(msg_send)

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
            await self.webSocket.send(response)

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
            await self.webSocket.send(response)


##############################################################

    async def reserve_now(self, message): 
        local_reservation_id = message[3]["reservationID"]
        local_connector_id = message[3]["connectorID"]
        if self.reservation_id == None or self.reservation_id == local_reservation_id:
            if self.ReserveConnectorZeroSupported == False and local_connector_id == 0:
                print("Connector zero not allowed")
                msg = [3,
                       # Have to use the unique message id received from server
                       message[1],
                       "ReserveNow",
                       {"status": "Rejected"}
                       ]
                msg_send = json.dumps(msg)
                await self.webSocket.send(msg_send)
                return
            self.hard_reset_reservation()
            self.is_reserved = True
            self.status = "Reserved"
            await asyncio.gather(self.send_status_notification(None))
            #state.set_state(States.S_FLEXICHARGEAPP)
            self.reservation_id_tag = int(message[3]["idTag"])
            self.reservation_id = message[3]["reservationID"]
            self.reserved_connector = message[3]["connectorID"]
            timestamp = message[3]["expiryDate"]  # Given in ms since epoch
            reserved_for_s = int(timestamp - int(time.time()))
            # reserved_for_ms/1000)   #Reservation time in seconds
            self.reserve_now_timer = int(reserved_for_s)
            self.timer_countdown_reservation  # Countdown every second

            msg = [3,
                   # Have to use the unique message id received from server
                   message[1],
                   "ReserveNow",
                   {"status": "Accepted"}
                   ]
            msg_send = json.dumps(msg)
            await self.webSocket.send(msg_send)
            return States.S_FLEXICHARGEAPP
        elif self.reserved_connector == local_connector_id:
            print("Connector occupied")
            msg = [3,
                   # Have to use the unique message id received from server
                   message[1],
                   "ReserveNow",
                   {"status": "Occupied"}
                   ]
            msg_send = json.dumps(msg)
            await self.webSocket.send(msg_send)
        else:
            print("Implement other messages for non accepted reservations")
            msg = [3,
                   # Have to use the unique message id received from server
                   message[1],
                   "ReserveNow",
                   {"status": "Occupied"}
                   ]
            msg_send = json.dumps(msg)
            await self.webSocket.send(msg_send)


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
        await self.webSocket.send(msg_send)
        pass

    async def start_charging_from_reservation(self):
        pass

    async def timer_countdown_reservation(self):
        pass

    async def timer_countdown_reservation(self):
        pass

    async def hard_reset_reservation(self):
        pass

    async def hard_reset_charging(self):
        pass
