from errno import WSAENOBUFS
from hashlib import new
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
from variables import charger_variables
from websocket_communication import WebSocket

from charger_hardware import Hardware

from variables.charger_variables import Charger
from variables.reservation_variables import Reservation
from variables.misc_variables import Misc

STATE = StateHandler()

CHARGER_GUI = UI(None)

hardware = Hardware()


#class ChargePoint():
#    my_websocket = "127.0.0.1:60003"
#    my_id = ""
#    charger = Charger()
#    misc = Misc()
#    reservation = Reservation()
#
#    # Send this to server at start and stop. It will calculate cost. Incremented during charging.
#    # ReserveConnectorZeroSupported  NEVER USED! why - Kevin and Elin 2022-09-14
#    reserve_connector_zero_supported = True
#
#    # Transaction related variables
#    transaction_id = None
#
#    # Define enums for status and error_code (or use the onses in OCPP library)
#    status = "Available"
#    error_code = "NoError"
#
#    hardcoded_connector_id = 1
#    hardcoded_vendor_id = "com.flexicharge"
#
#    hardcoded_id_tag = 1
#
#    charger_id = 000000
#
#    reserve_now_timer = 0
#    is_reserved = False
#    reservation_id_tag = None
#    reservation_id = None
#    reserved_connector = None
#    ReserveConnectorZeroSupported = True
#
#    timestamp_at_last_heartbeat: float = time.perf_counter()
#    # In seconds (heartbeat should be sent once every 24h)
#    time_between_heartbeats = 60 * 60 * 24
#
#    def __init__(self, id, connection):
#        self.my_websocket = connection
#        self.my_id = id

 

##########################################################################################################################

###########################################################################################################

    

async def choose_state(choosen_state: StateHandler):
    while True:
            CHARGER_GUI.change_state(choosen_state)

          
        


async def statemachine(webSocket: WebSocket):
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
    variables_charger = Charger() 
    variables_misc = Misc()
    variables_reservation = Reservation()
    
    new_state = await asyncio.gather(webSocket.get_message(variables_charger,variables_misc,variables_reservation))
    STATE.set_state(new_state)
    variables_misc.status, variables_charger.charger_id = await webSocket.update_charger_data()
    if variables_misc.status == "Available":
            while variables_charger.charger_id == 000000: #hw.getchargerid
                pass

    # chargerGUI.change_state(state.get_state())

    if variables_charger.charger_id == 000000:
        STATE.set_state(States.S_NOTAVAILABLE)
        CHARGER_GUI.change_state(STATE.get_state())
        while True:
            STATE.set_state(States.S_NOTAVAILABLE)
            # Display QR code image
            CHARGER_GUI.change_state(STATE.get_state())

    charger_ID = variables_charger.charger_id

    first_number_of_charger_id = int(charger_ID % 10)
    second_number_of_charger_id = int(charger_ID/10) % 10
    third_number_of_charger_id = int(charger_ID/100) % 10
    fouth_number_of_charger_id = int(charger_ID/1000) % 10
    fifth_number_of_charger_id = int(charger_ID/10000) % 10
    sixth_number_of_charger_id = int(charger_ID/100000) % 10

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
        new_state  = await asyncio.gather(webSocket.get_message(variables_charger,variables_misc,variables_reservation))
        STATE.set_state(new_state)
        variables_misc.status, variables_charger.charger_id = webSocket.update_charger_data()
        if variables_misc.status == "ReserveNow":

          variables_reservation.is_reserved, variables_misc.status,
          variables_reservation.reservation_id_tag,
          variables_reservation.reservation_id,
          variables_reservation.reserved_connector,
          variables_reservation.reserve_now_timer = await webSocket.get_reservation_info()

        if STATE.get_state() == States.S_STARTUP:
            CHARGER_GUI.change_state(STATE.get_state())
            continue

        elif STATE.get_state() == States.S_AVAILABLE:
            CHARGER_GUI.set_charger_id(charger_ID)
            variables_misc.status, variables_charger.charger_id = await webSocket.update_charger_data()
            CHARGER_GUI.change_state(STATE.get_state())

        elif STATE.get_state() == States.S_FLEXICHARGEAPP:
            CHARGER_GUI.change_state(STATE.get_state())
            print("flexichargeapp")

        elif STATE.get_state() == States.S_PLUGINCABLE:
            CHARGER_GUI.change_state(STATE.get_state())

        elif STATE.get_state() == States.S_CONNECTING:
            CHARGER_GUI.change_state(STATE.get_state())

        elif STATE.get_state() == States.S_CHARGING:
            num_of_secs = 100
            percent = 0
            timestamp_at_last_transfer = 0
            CHARGER_GUI.change_state(STATE.get_state())
            while True:
                await asyncio.gather(webSocket.get_message(variables_charger,variables_misc,variables_reservation))

                if variables_misc.status != "Charging":
                    STATE.set_state(States.S_AVAILABLE)
                    CHARGER_GUI.change_state(STATE.get_state())
                    break

                if (time.time() - timestamp_at_last_transfer) >= 1:
                    timestamp_at_last_transfer = time.time()
                    await asyncio.gather(webSocket.send_data_transfer(1, percent))
                if percent >= 100:
                    await asyncio.gather(webSocket.stop_transaction(False))
                    STATE.set_state(States.S_BATTERYFULL)
                    break

                time.sleep(1)
                percent += 1
                num_of_secs -= 1
                CHARGER_GUI.set_charge_precentage(percent)
                CHARGER_GUI.num_of_secs(num_of_secs)

        elif STATE.get_state() == States.S_BATTERYFULL:
            lastPrice = 50
            CHARGER_GUI.last_price(lastPrice)
            CHARGER_GUI.change_state(STATE.get_state())
            await asyncio.sleep(5)
            STATE.set_state(States.S_AVAILABLE)
            CHARGER_GUI.change_state(STATE.get_state())

async def main():
    """
    It connects to a websocket server, sends a boot notification, and then runs a state machine
    """
    try:
        ws = WebSocket()
        await ws.connect()
        asyncio.get_event_loop().run_until_complete(await statemachine(ws))

    except Exception as e:
        print("ERROR:")
        print(e)

if __name__ == '__main__':
    asyncio.run(main())
