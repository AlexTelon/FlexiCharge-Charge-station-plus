import datetime
from importlib.resources import is_resource
import json
import threading
import time
import websockets
import asyncio
from config import Configurations

class WebSocket():
#FUNCTIONS AND VARIABLES ARE RELEVANT TO WEB SOCKETS. THIS FILE IS TO EVALUATE HOW WEBSOCKET
#IS TO BE USED 
    my_websocket = None
    my_id = ""

    # Send this to server at start and stop. It will calculate cost. Incremented during charging.
    meter_value_total = 0
    current_charging_percentage = 0

    # Reservation related variables
    reserve_now_timer = 0
    is_reserved = False
    reservation_id_tag = None
    reservation_id = None
    reserved_connector = None
    ReserveConnectorZeroSupported = True

    # Transaction related variables
    is_charging = False
    charging_id_tag = None
    charging_connector = None
    charging_Wh = 0  # I think this is how many Wh have been used to charge
    transaction_id = None

    # Define enums for status and error_code (or use the onses in OCPP library)
    status = "Available"
    error_code = "NoError"

    hardcoded_connector_id = 1
    hardcoded_vendor_id = "com.flexicharge"

    hardcoded_id_tag = 1

    charger_id = 00000

    timestamp_at_last_heartbeat: float = time.perf_counter()
    # In seconds (heartbeat should be sent once every 24h)
    time_between_heartbeats = 60 * 60 * 24


    def __init__(self, id, connection):
        self.my_websocket = connection
        self.my_id = id

    async def get_message(self):
        """
        It checks for a message from the server, if it gets one, it checks the message type and calls
        the appropriate function.
        """
        c = 0
        while c < 3:
            c = c + 1
            try:
                msg = await asyncio.wait_for(self.my_websocket.recv(), 0.1)
                # async for msg in self.my_websocket: #Takes latest message
                print("Check for message")
                message = json.loads(msg)
                print(message)

                if message[2] == "ReserveNow":
                    await asyncio.gather(self.reserve_now(message))
                elif message[2] == "BootNotification":
                    message_str = str(message[3]["status"])
                    if message_str == "Accepted":
                        self.status = "Available"
                        state.set_state(States.S_AVAILABLE)
                        # Status notification should be sent after a boot
                        await asyncio.gather(self.send_status_notification(None))
                    else:
                        self.status = "Faulted"
                        await asyncio.gather(self.send_status_notification(None))
                        state.set_state(States.S_NOTAVAILABLE)
                elif message[2] == "RemoteStartTransaction":
                    await asyncio.gather(self.remote_start_transaction(message))
                elif message[2] == "RemoteStopTransaction":
                    await asyncio.gather(self.remote_stop_transaction(message))
                elif message[2] == "DataTransfer":
                    await asyncio.gather(self.recive_data_transfer(message))
                elif message[2] == "StartTransaction":
                    # self.transaction_id = message[3]["transactionId"]    #Store transaction id from server
                    self.transaction_id = 347
            except:
                pass
    
    # If the idTag has a reservation, start charging from the reservation, set the state to charging,
    # send a response to the central system, start the transaction, set the status to charging, and
    # send a status notification to the central system.
    # :param message: [3, "Unique message id", "RemoteStartTransaction", {"idTag": "12345"}]
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
            state.set_state(States.S_CHARGING)
            msg = [3,
                message[1],  # Unique message id
                "RemoteStartTransaction",
                {"status": "Accepted"}
                ]
            response = json.dumps(msg)
            await self.my_websocket.send(response)

            await self.start_transaction(is_remote=True)
            self.status = "Charging"
            # Notify central system that connector is now available
            await self.send_status_notification(None)
            print("Charge should be started")
        else:  # A non reserved tag tries to use the connector
            print("This tag does not have a reservation")
            msg = [3,
                message[1],  # Unique message id
                "RemoteStartTransaction",
                {"status": "Rejected"}
                ]
            response = json.dumps(msg)
            await self.my_websocket.send(response)
    
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
                await self.my_websocket.send(msg_send)
                return
            self.hard_reset_reservation()
            self.is_reserved = True
            self.status = "Reserved"
            await asyncio.gather(self.send_status_notification(None))
            state.set_state(States.S_FLEXICHARGEAPP)
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
            await self.my_websocket.send(msg_send)

        elif self.reserved_connector == local_connector_id:
            print("Connector occupied")
            msg = [3,
                   # Have to use the unique message id received from server
                   message[1],
                   "ReserveNow",
                   {"status": "Occupied"}
                   ]
            msg_send = json.dumps(msg)
            await self.my_websocket.send(msg_send)
        else:
            print("Implement other messages for non accepted reservations")
            msg = [3,
                   # Have to use the unique message id received from server
                   message[1],
                   "ReserveNow",
                   {"status": "Occupied"}
                   ]
            msg_send = json.dumps(msg)
            await self.my_websocket.send(msg_send)

    
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
            await self.my_websocket.send(msg_send)
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
            await self.my_websocket.send(msg_send)

    async def stop_transaction(self, is_remote):
        """
        It stops the transaction and sends a message to the server.

        :param is_remote: Boolean
        """
        current_time = datetime.now()
        timestamp = current_time.timestamp()
        self.status = "Available"
        await asyncio.gather(self.send_status_notification(None))
        if is_remote == True:
            msg = [2, "0jdsEnnyo2kpCP8FLfHlNpbvQXosR5ZNlh8v", "StopTransaction", {
                "idTag": self.charging_id_tag,
                "meterStop": self.meter_value_total,
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
            await self.my_websocket.send(msg_send)
            self.hard_reset_charging()
        else:
            msg = [2, "0jdsEnnyo2kpCP8FLfHlNpbvQXosR5ZNlh8v", "StopTransaction", {
                "idTag": self.charging_id_tag,
                "meterStop": self.meter_value_total,
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
            await self.my_websocket.send(msg_send)
            self.hard_reset_charging()

        response = await self.my_websocket.recv()
        print(json.loads(response))

    
    # Gets no response, is this an error in back-end? Seems to be the case
    async def send_status_notification(self, info):
        """
        It sends a message to the back-end with the status of the charging station.

        :param info: A string that contains information about the status
        """
        current_time = datetime.now()
        # Can be removed if back-end does want the time-stamp formated
        timestamp = current_time.timestamp()
        # Can be removed if back-end does not want the time-stamp formated
        formated_timestamp = current_time.strftime("%Y-%m-%dT%H:%M:%SZ")

        msg = [2, "0jdsEnnyo2kpCP8FLfHlNpbvQXosR5ZNlh8v", "StatusNotification", {
            "connectorId": self.hardcoded_connector_id,
            "errorCode": self.error_code,
            "info": info,  # Optional according to official OCPP-documentation
            "status": self.status,
            "timestamp": timestamp,  # Optional according to official OCPP-documentation
            # Optional according to official OCPP-documentation
            "vendorId": self.hardcoded_vendor_id,
            "vendorErrorCode": "None"  # Optional according to official OCPP-documentation
        }]

        msg_send = json.dumps(msg)
        await self.my_websocket.send(msg_send)
        print("Status notification sent with message: ")
        print(msg)
        self.timestamp_at_last_status_notification = time.perf_counter()

        #Depricated in back-end
    async def send_heartbeat(self):
        """
        It sends a heartbeat message to the websocket server
        """
        msg = [2, "0jdsEnnyo2kpCP8FLfHlNpbvQXosR5ZNlh8v", "Heartbeat", {}]
        msg_send = json.dumps(msg)
        await self.my_websocket.send(msg_send)
        # print(await self.my_websocket.recv())
        # await asyncio.sleep(1)
        self.timestamp_at_last_heartbeat = time.perf_counter()

    
    #Depricated in back-end
    async def send_meter_values(self):
        """
        It sends a message to the back-end with the sampled values
        """
        current_time = datetime.now()
        # Can be removed if back-end does want the time-stamp formated
        timestamp = current_time.timestamp()
        # Can be removed if back-end does not want the time-stamp formated
        formated_timestamp = current_time.strftime("%Y-%m-%dT%H:%M:%SZ")

        # Should be replace with "real" sampled values (this is just for testing)
        sample_value = "12345"
        sample_context = "Sample.Clock"
        sample_format = "Raw"
        sample_measurand = "Energy.Active.Export.Register"
        sample_phase = "L1"
        sample_location = "Cable"
        sample_unit = "kWh"

        msg = [2, "0jdsEnnyo2kpCP8FLfHlNpbvQXosR5ZNlh8v", "MeterValues", {
            "connectorId": self.hardcoded_connector_id,
            "transactionId": self.transaction_id,
            "meterValue": [{
                "timestamp": formated_timestamp,
                "sampledValue": [
                    {"value": sample_value,
                     "context": sample_context,
                     "format": sample_format,
                     "measurand": sample_measurand,
                     "phase": sample_phase,
                     "location": sample_location,
                     "unit": sample_unit},
                ]
            }, ],
        }]

        msg_send = json.dumps(msg)
        await self.my_websocket.send(msg_send)

    
    async def send_data_transfer(self, message_id, message_data):
        """
        I'm trying to send a JSON string to the server, but the server is expecting a JSON object

        :param message_id: The message ID of the message you want to send
        :param message_data: This is the data that is being sent to the server
        """
        s: str = "{}{}{}{}{}{}{}".format("{\"transactionId\":", self.transaction_id,
                                         ",\"latestMeterValue\":", message_data, ",\"CurrentChargePercentage\":", message_data, "}")
        print(s)

        msg = [2, "0jdsEnnyo2kpCP8FLfHlNpbvQXosR5ZNlh8v", "DataTransfer", {
            # "vendorId" : self.hardcoded_vendor_id,
            "messageId": "ChargeLevelUpdate",
            "data": s
        }]

        msg_send = json.dumps(msg)
        await self.my_websocket.send(msg_send)

    async def recive_data_transfer(self, message):
        """
        It receives a message from the server, checks if the vendorId is correct, if it is, it checks if
        the messageId is correct, if it is, it parses the data and sets the charger_id to the parsed
        data

        :param message: The message received from the websocket
        """
        status = "Rejected"
        if message[3]["vendorId"] == self.hardcoded_vendor_id:
            if message[3]["messageId"] == "BootData":
                parsed_data = json.loads(message[3]["data"])
                self.charger_id = parsed_data["chargerId"]
                print("Charger ID is set to: " + str(self.charger_id))
                status = "Accepted"
            else:
                status = "UnknownMessageId"
        else:
            status = "UnknownVenorId"

        # Send a conf
        conf_msg = [3,
                    message[1],
                    "DataTransfer",
                    {"status": status}]

        conf_send = json.dumps(conf_msg)
        print("Sending confirmation: " + conf_send)
        await self.my_websocket.send(conf_send)

    async def send_data_reserve(self):
        """
        It sends a message to the server, which is a list of two strings.
        """
        msg = ["chargerplus", "ReserveNow"]
        msg_send = json.dumps(msg)
        await self.my_websocket.send(msg_send)

    async def send_data_remote_start(self):
        """
        It sends a message to the websocket server, which then sends a message to the car.
        """
        msg = ["chargerplus", "RemoteStart"]
        msg_send = json.dumps(msg)
        await self.my_websocket.send(msg_send)

    async def send_data_remote_stop(self):
        """
        It sends a message to the websocket server to stop the charging session
        """
        msg = ["chargerplus", "RemoteStop"]
        msg_send = json.dumps(msg)
        await self.my_websocket.send(msg_send)



    


        