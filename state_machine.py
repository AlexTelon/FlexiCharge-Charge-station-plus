# from curses import window
from sre_parse import State
from charger_ui import UI
import asyncio
import json
import threading
import time
from datetime import datetime

import PySimpleGUI as sg
import qrcode
import websockets

from StateHandler import StateHandler
from StateHandler import States

from charger_hardware import Hardware

from variables.charger_variables import Charger
from variables.reservation_variables import Reservation
from variables.misc_variables import Misc

state = StateHandler()

charger_gui = UI(None)

hardware = Hardware()


class ChargePoint():
    my_websocket = "127.0.0.1:60003"
    my_id = ""
    charger = Charger()
    misc = Misc()
    reservation = Reservation()

    # Send this to server at start and stop. It will calculate cost. Incremented during charging.
    # ReserveConnectorZeroSupported  NEVER USED! why - Kevin and Elin 2022-09-14
    reserve_connector_zero_supported = True

    # Transaction related variables
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

    # AuthorizeRemoteTxRequests is always false since no authorize function exists in backend(?)
    # TODO - Change when multiple connectors exists. Add parent id tag.
    #       No handling for connectorID = 0 since only a single connector will exist in mvp
    #       No status_notification is sent since it does not get a response and locks the program
    async def remote_start_transaction(self, message):
        """
        If the idTag has a reservation, start charging from the reservation, set the state to charging,
        send a response to the central system, start the transaction, set the status to charging, and
        send a status notification to the central system.
        :param message: [3, "Unique message id", "RemoteStartTransaction", {"idTag": "12345"}]
        """
        if int(message[3]["idTag"]) == self.reservation.reservation_id_tag:  # If the idTag has a reservation
            self.hardware.start_charging_from_reservation()
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
        if self.charger.is_charging == True:
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


##########################################################################################################################


    def send_periodic_meter_values(self):
        """
        It sends the current charging percentage to the server every 2 seconds, and if the car is
        charging, it starts the function again
        """
        asyncio.run(self.send_data_transfer(
            1, self.charger.current_charging_percentage))
        if self.charger.current_charging_percentage:
            threading.Timer(2, self.send_periodic_meter_values).start()

    async def reserve_now(self, message):
        local_reservation_id = message[3]["reservationID"]
        local_connector_id = message[3]["connectorID"]
        if self.reservation.reservation_id == None or self.reservation.reservation_id == local_reservation_id:
            # This if is never user ReserveConnectorZeroSupported is ALWAYS True - Kevin and Elin 2022-09-14
            if self.reserve_connector_zero_supported == False and local_connector_id == 0:
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
            self.hardware.hard_reset_reservation()
            self.reservation.is_reserved = True
            self.status = "Reserved"
            await asyncio.gather(self.send_status_notification(None))
            state.set_state(States.S_FLEXICHARGEAPP)
            self.reservation.reservation_id_tag = int(message[3]["idTag"])
            self.reservation.reservation_id = message[3]["reservationID"]
            self.reservation.reserved_connector = message[3]["connectorID"]
            timestamp = message[3]["expiryDate"]  # Given in ms since epoch
            reserved_for_s = int(timestamp - int(time.time()))
            # reserved_for_ms/1000)   #Reservation time in seconds
            self.reservation.reserve_now_timer = int(reserved_for_s)
            self.hardware.timer_countdown_reservation  # Countdown every second

            msg = [3,
                   # Have to use the unique message id received from server
                   message[1],
                   "ReserveNow",
                   {"status": "Accepted"}
                   ]
            msg_send = json.dumps(msg)
            await self.my_websocket.send(msg_send)

        elif self.reservation.reserved_connector == local_connector_id:
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
###################################################################################################################
    # Tells server we have started a transaction (charging)

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
                "connectorId": self.charger.charging_connector,
                "id_tag": self.charger.charging_id_tag,  # This is suppose to be the RFID tag
                "meterStart": self.misc.meter_value_total,
                "timestamp": timestamp,
                "reservationId": self.reservation.reservation_id,
            }]

            self.hardware.hard_reset_reservation()
            msg_send = json.dumps(msg)
            await self.my_websocket.send(msg_send)
        else:  # No reservation
            self.hardware.start_charging(self.hardcoded_connector_id,
                                         self.hardcoded_id_tag)

            msg = [2, "0jdsEnnyo2kpCP8FLfHlNpbvQXosR5ZNlh8v", "StartTransaction", {
                "connectorId": self.charger.charging_connector,
                "id_tag": self.charger.charging_id_tag,
                "meterStart": self.misc.meter_value_total,
                "timestamp": timestamp,
                "reservationId": None,  # If here, no reservation was made
            }]

            msg_send = json.dumps(msg)
            await self.my_websocket.send(msg_send)

    # TODO - Adjust to multiple connectors when added. Assumes a single connector
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
            await self.my_websocket.send(msg_send)
            self.hardware.hard_reset_charging()
        else:
            msg = [2, "0jdsEnnyo2kpCP8FLfHlNpbvQXosR5ZNlh8v", "StopTransaction", {
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
            await self.my_websocket.send(msg_send)
            self.hardware.hard_reset_charging()

        response = await self.my_websocket.recv()
        print(json.loads(response))

    async def send_boot_notification(self):
        """
        I'm trying to send a message to the server, but I'm getting an error
        """
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
        await self.my_websocket.send(msg_send)

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

    # Depricated in back-end
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

    async def check_if_time_for_heartbeat(self):
        """
        If the time since the last heartbeat is greater than or equal to the time between heartbeats,
        return True. Otherwise, return False.
        :return: a boolean value.
        """
        seconds_since_last_heartbeat = time.perf_counter() - \
            (self.timestamp_at_last_heartbeat)
        if seconds_since_last_heartbeat >= self.time_between_heartbeats:
            return True
        else:
            return False

    # Depricated in back-end
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
###########################################################################################################

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
                print("Charger ID is set to: " + str(self.charger.charging_id))
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


async def choose_state(choosen_state: StateHandler):
    while True:
            charger_gui.change_state(choosen_state)

          
        


async def statemachine(charge_point: ChargePoint):
    """
    The function is a state machine that changes the state of the charge point and displays the relevant
    image on the screen
    :param chargePoint: The ChargePoint object that is used to communicate with the OCPP server
    :type chargePoint: ChargePoint
    """
    # -- Variable not used : global window_back, window_qrCode

    # instead of chargerID = 128321 you have to write the follwoing two rows(your ocpp code) to get
    # the charge id from back-end and display it on screen

    # response = await ocpp_client.send_boot_notification()
    # chargerID = response.charger_id

    """  for i in range(20):
        await asyncio.gather(chargePoint.get_message())
        if chargePoint.charger_id != 000000:
            break """

    # chargerGUI.change_state(state.get_state())

    charger_id = charge_point.charger_id

    first_number_of_charger_id = int(charger_id % 10)
    second_number_of_charger_id = int(charger_id/10) % 10
    third_number_of_charger_id = int(charger_id/100) % 10
    fouth_number_of_charger_id = int(charger_id/1000) % 10
    fifth_number_of_charger_id = int(charger_id/10000) % 10
    sixth_number_of_charger_id = int(charger_id/100000) % 10

    charger_id_layout = [
        [
            sg.Text(sixth_number_of_charger_id, font=(
                'Tw Cen MT Condensed Extra Bold', 30), key='ID5', justification='center', pad=(25, 0)),
            sg.Text(fifth_number_of_charger_id, font=(
                'Tw Cen MT Condensed Extra Bold', 30), key='ID4', justification='center', pad=(20, 0)),
            sg.Text(fouth_number_of_charger_id, font=(
                'Tw Cen MT Condensed Extra Bold', 30), key='ID3', justification='center', pad=(25, 0)),
            sg.Text(third_number_of_charger_id, font=(
                'Tw Cen MT Condensed Extra Bold', 30), key='ID2', justification='center', pad=(20, 0)),
            sg.Text(second_number_of_charger_id, font=(
                'Tw Cen MT Condensed Extra Bold', 30), key='ID1', justification='center', pad=(25, 0)),
            sg.Text(first_number_of_charger_id, font=(
                'Tw Cen MT Condensed Extra Bold', 30), key='ID0', justification='center', pad=(20, 0))
        ]
    ]

    charger_id_window = sg.Window(title="FlexiChargeTopWindow", layout=charger_id_layout, location=(15, 735), keep_on_top=True,
                                  grab_anywhere=False, transparent_color='white', background_color='white', size=(470, 75), no_titlebar=True).finalize()
    charger_id_window.TKroot["cursor"] = "none"
    charger_id_window.hide()

    while True:
        await asyncio.gather(charge_point.get_message())

        if state.get_state() == States.S_STARTUP:
            charger_gui.change_state(state.get_state())
            continue

        elif state.get_state() == States.S_AVAILABLE:
            charger_gui.set_charger_id(charger_id)
            charger_gui.change_state(state.get_state())

        elif state.get_state() == States.S_FLEXICHARGEAPP:
            charger_gui.change_state(state.get_state())
            print("flexichargeapp")

        elif state.get_state() == States.S_PLUGINCABLE:
            charger_gui.change_state(state.get_state())

        elif state.get_state() == States.S_CONNECTING:
            charger_gui.change_state(state.get_state())

        elif state.get_state() == States.S_CHARGING:
            num_of_secs = 100
            percent = 0
            timestamp_at_last_transfer = 0
            charger_gui.change_state(state.get_state())
            while True:
                await asyncio.gather(charge_point.get_message())

                if charge_point.status != "Charging":
                    state.set_state(States.S_AVAILABLE)
                    charger_gui.change_state(state.get_state())
                    break

                if (time.time() - timestamp_at_last_transfer) >= 1:
                    timestamp_at_last_transfer = time.time()
                    await asyncio.gather(charge_point.send_data_transfer(1, percent))
                if percent >= 100:
                    await asyncio.gather(charge_point.stop_transaction(False))
                    state.set_state(States.S_BATTERYFULL)
                    break

                time.sleep(1)
                percent = percent + 1
                num_of_secs = num_of_secs - 1
                charger_gui.set_charge_precentage(percent)
                charger_gui.num_of_secs(num_of_secs)

        elif state.get_state() == States.S_BATTERYFULL:
            lastPrice = 50
            charger_gui.last_price(lastPrice)
            charger_gui.change_state(state.get_state())
            await asyncio.sleep(5)
            state.set_state(States.S_AVAILABLE)
            charger_gui.change_state(state.get_state())

async def main():
    """
    It connects to a websocket server, sends a boot notification, and then runs a state machine
    """

     #try:
    async with websockets.connect(
            'ws://127.0.0.1:60003',
            subprotocols=['ocpp1.6'],
            ping_interval=5,
            timeout = None
        ) as ws:
     charge_point = ChargePoint('0jdsEnnyo2kpCP8FLfHlNpbvQXosR5ZNlh8v', ws)
     await charge_point.send_boot_notification()
     #asyncio.get_event_loop().run_until_complete(await statemachine(charge_point))
     asyncio.get_event_loop().run_until_complete(await choose_state(States.S_FLEXICHARGEAPP))
     #asyncio.get_event_loop().run_until_complete(await choose_state(States.S_CHARGING))
     
    # except:
    # print("Websocket error: Could not connect to server!")
    # Ugly? Yes! Works? Yes! (Should might use the statemachine but that will generate problems due to the websocket not working, due to the lack of time i won't fix that now)


if __name__ == '__main__':
    asyncio.run(main())
