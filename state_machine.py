from hashlib import new
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
import variables
from websocket_communication import WebSocket

from charger_hardware import Hardware

from variables.charger_variables import Charger
from variables.reservation_variables import Reservation


STATE = StateHandler()
CHARGER_GUI = UI(States.S_STARTUP)
CHARGER_VARIABLES = Charger()


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
    print("STATEMACHINE")
    task = asyncio.create_task(webSocket.start_websocket())
    await asyncio.sleep(0.2)
    CHARGER_VARIABLES = webSocket.update_charger_variables()

    chargerID = CHARGER_VARIABLES.charger_id

    firstNumberOfChargerID = int(chargerID % 10)
    secondNumberOfChargerID = int(chargerID/10) % 10
    thirdNumberOfChargerID = int(chargerID/100) % 10
    fouthNumberOfChargerID = int(chargerID/1000) % 10
    fifthNumberOfChargerID = int(chargerID/10000) % 10
    sixthNumberOfChargerID = int(chargerID/100000) % 10

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
        # try:
        #    await asyncio.gather(webSocket.get_message())
        # except Exception as e:
        #    print("EXEPTION FROM STATMACHINE: {}".format(e))
        await asyncio.sleep(1)
        CHARGER_VARIABLES = webSocket.update_charger_variables()
        STATE.set_state(CHARGER_VARIABLES.current_state)
        CHARGER_GUI.change_state(CHARGER_VARIABLES.current_state)
        if CHARGER_VARIABLES.status == "ReserveNow":
            Reservation.is_reserved, CHARGER_VARIABLES.status,
            Reservation.reservation_id_tag,
            Reservation.reservation_id,
            Reservation.reserved_connector,
            Reservation.reserve_now_timer = await webSocket.get_reservation_info
        if STATE.get_state() == States.S_STARTUP:
            CHARGER_GUI.change_state(STATE.get_state())
            continue

        elif STATE.get_state() == States.S_AVAILABLE:
            CHARGER_GUI.set_charger_id(chargerID)
            CHARGER_GUI.change_state(STATE.get_state())

        elif STATE.get_state() == States.S_FLEXICHARGEAPP:
            CHARGER_GUI.change_state(STATE.get_state())

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
                # await asyncio.gather(webSocket.get_message())

                if CHARGER_VARIABLES.status != "Charging":
                    STATE.set_state(States.S_AVAILABLE)
                    CHARGER_GUI.change_state(STATE.get_state())
                    break

                if (time.time() - timestamp_at_last_transfer) >= 1:
                    timestamp_at_last_transfer = time.time()
                    # await asyncio.gather(webSocket.send_data_transfer(1, percent)) #send_data_transfer function has not been implemented
                if percent == 100:
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
    It connects to a websocket server and then runs a state machine
    """
    try:
        webSocket = WebSocket()

        # await task
        #print("WebSocket close status: {}".format(webSocket._webSocket.closed))
        # webSocket._webSocket.closed: True
        # asyncio.get_event_loop().run_until_complete(statemachine(webSocket))
        await(statemachine(webSocket))

    except Exception as e:
        print("ERROR:")
        print(e)


if __name__ == '__main__':
    asyncio.run(main())
