from ctypes.wintypes import CHAR
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
from variables import charger_variables
from websocket_communication import WebSocket

from charger_hardware import Hardware

from variables.charger_variables import Charger
from variables.reservation_variables import Reservation


STATE = StateHandler()
CHARGER_GUI = UI()
CHARGER_VARIABLES = Charger()
full_time = CHARGER_VARIABLES.current_charge_time_left


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

    while True:

        await asyncio.sleep(1)
        CHARGER_VARIABLES = webSocket.update_charger_variables()
        print(str(CHARGER_VARIABLES.current_state))
        print(str(CHARGER_VARIABLES.current_state))
        CHARGER_GUI.change_state(CHARGER_VARIABLES.current_state)

        state = CHARGER_VARIABLES.current_state
        if CHARGER_VARIABLES.status == "ReserveNow":
            Reservation.is_reserved, CHARGER_VARIABLES.status,
            Reservation.reservation_id_tag,
            Reservation.reservation_id,
            Reservation.reserved_connector,
            Reservation.reserve_now_timer = await webSocket.get_reservation_info

        if state == States.S_STARTUP:
            CHARGER_GUI.change_state(state)

        elif state == States.S_AVAILABLE:
            CHARGER_VARIABLES.current_charge_time_left = CHARGER_VARIABLES.CHARGE_TIME_MAX
            CHARGER_GUI.set_charger_id(CHARGER_VARIABLES.charger_id)
            CHARGER_GUI.change_state(state)

        elif state == States.S_FLEXICHARGEAPP:
            CHARGER_GUI.change_state(state)

        elif state == States.S_PLUGINCABLE:
            CHARGER_GUI.change_state(state)

        elif state == States.S_CONNECTING:
            CHARGER_GUI.change_state(state)

        elif state == States.S_CHARGING:
            time_left = CHARGER_VARIABLES.current_charge_time_left
    
            timestamp_at_last_transfer = 0
            CHARGER_GUI.change_state(state)
            
            print("CHARGING")
            print(CHARGER_VARIABLES.status)
            if CHARGER_VARIABLES.status != "Charging":
                CHARGER_VARIABLES.current_state = States.S_AVAILABLE

            try:
                if (time.time() - timestamp_at_last_transfer) >= 1:
                    timestamp_at_last_transfer = time.time()
                    await asyncio.gather(webSocket.send_meter_values())
            except Exception as e:
                print(str(e))
            
            if CHARGER_VARIABLES.current_charging_percentage >= 100:
                await asyncio.gather(webSocket.stop_transaction(True))
                CHARGER_VARIABLES.current_state = States.S_BATTERYFULL
    

            CHARGER_VARIABLES.current_charging_percentage += 10
            CHARGER_VARIABLES.current_charge_time_left -= 1
            CHARGER_GUI.set_charge_precentage(CHARGER_VARIABLES.current_charging_percentage)
            CHARGER_GUI.set_power_charged(round((full_time - time_left)* CHARGER_VARIABLES.charging_Wh_per_second,2))
            try:
                CHARGER_GUI.set_num_of_secs(time_left)
            except Exception as e:
                print(str(e))
            print("GUI UPDATED")

        elif state == States.S_BATTERYFULL:
            CHARGER_GUI.change_state(state)
            CHARGER_VARIABLES.current_state = States.S_AVAILABLE
            lastPrice = 50
            CHARGER_GUI.set_last_price(lastPrice)
            await asyncio.sleep(5)
            CHARGER_GUI.change_state(state)
            


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
