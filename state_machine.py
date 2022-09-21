from hashlib import new
from chargerui import ChargerGUI
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
from web_socket_test_class import WebSocket

from charger_hardware import Hardware
from get_set_variables import Get
from get_set_variables import Set

state = StateHandler()
chargerGUI = ChargerGUI(States.S_STARTUP)

class ChargePoint():
    hardware = Hardware()
    get = Get()
    set = Set()
    # Send this to server at start and stop. It will calculate cost. Incremented during charging.
    # ReserveConnectorZeroSupported  NEVER USED! why - Kevin and Elin 2022-09-14
    ReserveConnectorZeroSupported = True
    webSocket : WebSocket = None
    # Transaction related variables
    transaction_id = None

    # Define enums for status and error_code (or use the onses in OCPP library)
    status = "Available"
    error_code = "NoError"

    hardcoded_connector_id = 1
    hardcoded_vendor_id = "com.flexicharge"

    hardcoded_id_tag = 1

    charger_id = 000000

    reserve_now_timer = 0
    is_reserved = False
    reservation_id_tag = None
    reservation_id = None
    reserved_connector = None
    ReserveConnectorZeroSupported = True

    timestamp_at_last_heartbeat: float = time.perf_counter()
    # In seconds (heartbeat should be sent once every 24h)
    time_between_heartbeats = 60 * 60 * 24

    def __init__(self, _webSocket: WebSocket):
        self.webSocket = _webSocket
    def send_periodic_meter_values(self):
        """
        It sends the current charging percentage to the server every 2 seconds, and if the car is
        charging, it starts the function again
        """
        asyncio.run(self.send_data_transfer(
            1, self.get.current_charging_percentage))
        if self.get.current_charging_percentage:
            threading.Timer(2, self.send_periodic_meter_values).start()



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

    #Depricated in back-end
 
###########################################################################################################

async def statemachine(chargePoint: ChargePoint):
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

    for _ in range(20):
        new_state = await asyncio.gather(chargePoint.webSocket.get_message())
        state.set_state(new_state)
        chargePoint.status, chargePoint.charger_id = chargePoint.webSocket.update_charger_data()
        if chargePoint.charger_id != 000000:
            break

    if chargePoint.charger_id == 000000:
        state.set_state(States.S_NOTAVAILABLE)
        chargerGUI.change_state(state.get_state())
        while True:
            state.set_state(States.S_NOTAVAILABLE)
            # Display QR code image
            chargerGUI.change_state(state.get_state())

    chargerID = chargePoint.charger_id

    firstNumberOfChargerID  = int(chargerID % 10)
    secondNumberOfChargerID = int(chargerID/10) % 10
    thirdNumberOfChargerID  = int(chargerID/100) % 10
    fouthNumberOfChargerID  = int(chargerID/1000) % 10
    fifthNumberOfChargerID  = int(chargerID/10000) % 10
    sixthNumberOfChargerID  = int(chargerID/100000) % 10

    chargerIdLayout = [
        [
            sg.Text(sixthNumberOfChargerID, font=(
                'Tw Cen MT Condensed Extra Bold', 30), key='ID5', justification='center', pad=(25, 0)),
            sg.Text(fifthNumberOfChargerID, font=(
                'Tw Cen MT Condensed Extra Bold', 30), key='ID4', justification='center', pad=(20, 0)),
            sg.Text(fouthNumberOfChargerID, font=(
                'Tw Cen MT Condensed Extra Bold', 30), key='ID3', justification='center', pad=(25, 0)),
            sg.Text(thirdNumberOfChargerID, font=(
                'Tw Cen MT Condensed Extra Bold', 30), key='ID2', justification='center', pad=(20, 0)),
            sg.Text(secondNumberOfChargerID, font=(
                'Tw Cen MT Condensed Extra Bold', 30), key='ID1', justification='center', pad=(25, 0)),
            sg.Text(firstNumberOfChargerID, font=(
                'Tw Cen MT Condensed Extra Bold', 30), key='ID0', justification='center', pad=(20, 0))
        ]
    ]

    chargerID_window = sg.Window(title="FlexiChargeTopWindow", layout=chargerIdLayout, location=(15, 735), keep_on_top=True,
                                 grab_anywhere=False, transparent_color='white', background_color='white', size=(470, 75), no_titlebar=True).finalize()
    chargerID_window.TKroot["cursor"] = "none"
    chargerID_window.hide()

    while True:
        new_state  = await asyncio.gather(chargePoint.webSocket.get_message())
        state.set_state(new_state)
        chargePoint.status, chargePoint.charger_id = chargePoint.webSocket.update_charger_data()
        if chargePoint.status == "ReserveNow":
          chargePoint.is_reserved, chargePoint.status, 
          chargePoint.reservation_id_tag, 
          chargePoint.reservation_id, 
          chargePoint.reserved_connector, 
          chargePoint.reserve_now_timer = chargePoint.webSocket.get_reservation_info()

        if state.get_state() == States.S_STARTUP:
            chargerGUI.change_state(state.get_state())
            continue

        elif state.get_state() == States.S_AVAILABLE:

            chargerGUI.set_charger_id(chargerID)
            chargerGUI.change_state(state.get_state())

        elif state.get_state() == States.S_FLEXICHARGEAPP:
            chargerGUI.change_state(state.get_state())

        elif state.get_state() == States.S_PLUGINCABLE:
            chargerGUI.change_state(state.get_state())

        elif state.get_state() == States.S_CONNECTING:
            chargerGUI.change_state(state.get_state())

        elif state.get_state() == States.S_CHARGING:
            num_of_secs = 100
            percent = 0
            timestamp_at_last_transfer = 0
            chargerGUI.change_state(state.get_state())
            while True:
                await asyncio.gather(chargePoint.webSocket.get_message())

                if chargePoint.status != "Charging":
                    state.set_state(States.S_AVAILABLE)
                    chargerGUI.change_state(state.get_state())
                    break

                if (time.time() - timestamp_at_last_transfer) >= 1:
                    timestamp_at_last_transfer = time.time()
                    await asyncio.gather(chargePoint.webSocket.send_data_transfer(1, percent))
                if percent == 100:
                    await asyncio.gather(chargePoint.webSocket.stop_transaction(False))
                    state.set_state(States.S_BATTERYFULL)
                    break

                time.sleep(1)
                percent = percent + 1
                num_of_secs = num_of_secs - 1
                chargerGUI.set_charge_precentage(percent)
                chargerGUI.num_of_secs(num_of_secs)

        elif state.get_state() == States.S_BATTERYFULL: 
            lastPrice = 50
            chargerGUI.last_price(lastPrice)
            chargerGUI.change_state(state.get_state())
            await asyncio.sleep(5)
            state.set_state(States.S_AVAILABLE)
            chargerGUI.change_state(state.get_state())


async def main():
    """
    It connects to a websocket server, sends a boot notification, and then runs a state machine
    """
    try:
        async with websockets.connect(
            'ws://18.202.253.30:1337/testnumber13',
            subprotocols=['ocpp1.6'],
            ping_interval=5,
            timeout = None
        ) as ws:

            webSocket = WebSocket("chargerplus", ws)
            chargePoint = ChargePoint(webSocket)
            await webSocket.send_boot_notification()
            await webSocket.send_heartbeat()
        asyncio.get_event_loop().run_until_complete(await statemachine(chargePoint))
    except:
        print("Websocket error: Could not connect to server!")
        # Ugly? Yes! Works? Yes! (Should might use the statemachine but that will generate problems due to the websocket not working, due to the lack of time i won't fix that now)
        chargeGUI = ChargerGUI(States.S_STARTUP)
        chargeGUI.change_state(States.S_NOTAVAILABLE)
       
if __name__ == '__main__':
    asyncio.run(main())
