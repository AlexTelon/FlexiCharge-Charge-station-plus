from errno import WSAENOBUFS
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
import variables
from websocket_communication import WebSocket

from charger_hardware import Hardware
from get_set_variables import Get
from get_set_variables import Set

from variables import charger_variables
from variables import reservation_variables
from variables import misc_variables


STATE = StateHandler()
CHARGER_GUI = ChargerGUI(States.S_STARTUP)
CHARGER_VARIABLES = charger_variables()


#lass ChargePoint():
#   hardware = Hardware()
#   get = Get()
#   set = Set()
#   # Send this to server at start and stop. It will calculate cost. Incremented during charging.
#   # ReserveConnectorZeroSupported  NEVER USED! why - Kevin and Elin 2022-09-14
#   ReserveConnectorZeroSupported = True
#   webSocket : WebSocket = None
#   # Transaction related variables
#   transaction_id = None
#
#   # Define enums for status and error_code (or use the onses in OCPP library)
#   status = "Available"
#   error_code = "NoError"
#
#   hardcoded_connector_id = 1
#   hardcoded_vendor_id = "com.flexicharge"
#
#   hardcoded_id_tag = 1
#
#   charger_id = 000000
#
#   reserve_now_timer = 0
#   is_reserved = False
#   reservation_id_tag = None
#   reservation_id = None
#   reserved_connector = None
#   ReserveConnectorZeroSupported = True
#
#   timestamp_at_last_heartbeat: float = time.perf_counter()
#   # In seconds (heartbeat should be sent once every 24h)
#   time_between_heartbeats = 60 * 60 * 24
#
#   def __init__(self, _webSocket: WebSocket):
#       self.webSocket = _webSocket
#   def send_periodic_meter_values(self):
#       """
#       It sends the current charging percentage to the server every 2 seconds, and if the car is
#       charging, it starts the function again
#       """
#       asyncio.run(self.send_data_transfer(
#           1, self.get.current_charging_percentage))
#       if self.get.current_charging_percentage:
#           threading.Timer(2, self.send_periodic_meter_values).start()
#
#
#
#   async def check_if_time_for_heartbeat(self):
#       """
#       If the time since the last heartbeat is greater than or equal to the time between heartbeats,
#       return True. Otherwise, return False.
#       :return: a boolean value.
#       """
#       seconds_since_last_heartbeat = time.perf_counter() - \
#           (self.timestamp_at_last_heartbeat)
#       if seconds_since_last_heartbeat >= self.time_between_heartbeats:
#           return True
#       else:
#           return False

    #Depricated in back-end

###########################################################################################################

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

    #These should probably not be here. Move to correct classes.

    
    variables_charger = charger_variables.Charger() 
    variables_misc = misc_variables.Misc()
    variables_reservation = reservation_variables.Reservation()
#
    new_state = await asyncio.gather(webSocket.get_message(variables_charger,variables_misc,variables_reservation))
    STATE.set_state(new_state)
    variables_misc.status, variables_charger.charger_id = await webSocket.update_charger_data()
    if variables_misc.status == "Available":
            while variables_charger.charger_id == 000000: #hw.getchargerid
                pass

    if variables_charger.charger_id == 000000:
        STATE.set_state(States.S_NOTAVAILABLE)
        CHARGER_GUI.change_state(STATE.get_state())
        while True:
            STATE.set_state(States.S_NOTAVAILABLE)
            # Display QR code image
            CHARGER_GUI.change_state(STATE.get_state())

    chargerID = variables_charger.charger_id

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

            CHARGER_GUI.set_charger_id(chargerID)
            variables_misc.status, variables_charger.charger_id = await webSocket.update_charger_data()
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
                await asyncio.gather(webSocket.get_message(variables_charger,variables_misc,variables_reservation))

                if variables_misc.status != "Charging":
                    STATE.set_state(States.S_AVAILABLE)
                    CHARGER_GUI.change_state(STATE.get_state())
                    break

                if (time.time() - timestamp_at_last_transfer) >= 1:
                    timestamp_at_last_transfer = time.time()
                    await asyncio.gather(webSocket.send_data_transfer(1, percent))
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
        ws = WebSocket()
        await ws.connect()
        asyncio.get_event_loop().run_until_complete(await statemachine(ws))

    except Exception as e:
        print("ERROR:")
        print(e)


if __name__ == '__main__':
    asyncio.run(main())