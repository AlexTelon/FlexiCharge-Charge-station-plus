from GUI.charger_ui import UI
import asyncio
import time
from StateHandler import States
from websocket_communication import WebSocket
from charger_hardware import Hardware
from variables.charger_variables import Charger
from variables.reservation_variables import Reservation

CHARGER_GUI = UI()
CHARGER_VARIABLES = Charger()
CHARGER = Hardware()

async def handle_startup_state(state):
    CHARGER_GUI.generate_qr_code(CHARGER_VARIABLES.charger_id)
    CHARGER_GUI.change_state(state)

async def handle_available_state(state):
    CHARGER_GUI.set_charger_id(CHARGER_VARIABLES.charger_id)
    CHARGER.update_timeout()
    CHARGER_GUI.change_state(state)

async def handle_not_available_state(state):
    CHARGER_GUI.change_state(state)

async def handle_plug_in_cable_state(state,webSocket):
    CHARGER_GUI.change_state(state)
    CHARGER.read_via_UART()
    CHARGER_VARIABLES = CHARGER.get_charger_variables()

    if CHARGER.timeout_passed_and_not_connected():
        CHARGER_VARIABLES.reset_variables()
        CHARGER_VARIABLES.current_state = States.S_AVAILABLE
        CHARGER.set_charger_variables(CHARGER_VARIABLES)

    if CHARGER_VARIABLES.is_connected:
        CHARGER_VARIABLES.current_state = States.S_CONNECTING

    webSocket.set_charger_variables(CHARGER_VARIABLES)

async def handle_connecting_state(state,webSocket):
    CHARGER_GUI.change_state(state)
    CHARGER.read_via_UART()
    CHARGER_VARIABLES = CHARGER.get_charger_variables()

    if CHARGER.timeout_passed_and_not_connected():
        CHARGER_VARIABLES.reset_variables()
        CHARGER_VARIABLES.current_state = States.S_AVAILABLE
        CHARGER.set_charger_variables(CHARGER_VARIABLES)

    if(CHARGER_VARIABLES.is_connected and CHARGER_VARIABLES.is_charging and CHARGER_VARIABLES.requsted_voltage != ""):
        CHARGER.controll_output_voltage(CHARGER_VARIABLES.requsted_voltage)
        CHARGER_VARIABLES.current_state = States.S_CHARGING

    webSocket.set_charger_variables(CHARGER_VARIABLES)

async def handle_charging_state(state,webSocket,charing_start_time):
    CHARGER_GUI.change_state(state)
    CHARGER.read_via_UART()
    CHARGER_VARIABLES = CHARGER.get_charger_variables()

    if not CHARGER.is_connected():
        CHARGER.controll_output_voltage("off")
        await asyncio.gather(webSocket.stop_transaction(True))
        CHARGER_VARIABLES.reset_variables()

    webSocket.set_charger_variables(CHARGER_VARIABLES)
    
    try:
        if (time.time() - charing_start_time) >= 1:
            current = CHARGER.read_current_from_INA219()
            voltage = CHARGER.read_voltage_from_INA219()
            power = CHARGER.calc_power(voltage, (current/1000))
            CHARGER.calc_power_hour(power, 1)
            CHARGER_VARIABLES = CHARGER.get_charger_variables()
            webSocket.set_charger_variables(CHARGER_VARIABLES)
            await asyncio.gather(webSocket.send_meter_values())
            charing_start_time = time.time()
    except Exception as e:
        print(str(e))

    CHARGER_GUI.set_charge_precentage(CHARGER_VARIABLES.current_charging_percentage)
    CHARGER_GUI.set_charging_price(CHARGER_VARIABLES.charging_price)
    CHARGER_GUI.set_power_charged(round(CHARGER_VARIABLES.charging_Wh,5))
    CHARGER_GUI.update_charging()

async def statemachine(webSocket: WebSocket):

    """
    The function is a state machine that changes the state of the charge point and displays the relevant
    image on the screen
    :param webSocket: The WebSocket object that is used to communicate with the OCPP server

    All states are not implemented. This is a todo for the next group
    """

    print("Entering State machine")
    task = asyncio.create_task(webSocket.start_websocket())     #Starts the websocket listening in a thread that is running in the backgound
    await asyncio.sleep(0.2)                                    #Make the state machine sleep in some time to give the background task a chance to run.
    CHARGER_VARIABLES = webSocket.get_charger_variables()
    CHARGER.set_charger_variables(CHARGER_VARIABLES)
    charing_start_time = 0
    while True:

        await asyncio.sleep(1)      #Make the state machine sleep in some time to give the background task a chance to run.
        
        CHARGER_VARIABLES = webSocket.get_charger_variables()
        CHARGER.set_charger_variables(CHARGER_VARIABLES)

        state = CHARGER_VARIABLES.current_state 

        if CHARGER_VARIABLES.status == "ReserveNow":
            Reservation.is_reserved, CHARGER_VARIABLES.status,
            Reservation.reservation_id_tag,
            Reservation.reservation_id,
            Reservation.reserved_connector = await webSocket.get_reservation_info()

        if state == States.S_STARTUP:
            await handle_startup_state(state)
        
        elif state == States.S_NOTAVAILABLE:
            await handle_not_available_state(state)

        elif state == States.S_AVAILABLE:
            await handle_available_state(state)

        elif state == States.S_PLUGINCABLE:
            await handle_plug_in_cable_state(state, webSocket)

        elif state == States.S_CONNECTING:
            await handle_connecting_state(state,webSocket)

        elif state == States.S_CHARGING:
            await handle_charging_state(state,webSocket,charing_start_time)            

async def main():
    """
    It initiates a WebSocket-object (from websocket_communication) and runs the state machine
    """
    try:
        webSocket = WebSocket()
        await(statemachine(webSocket))

    except Exception as e:
        print("ERROR: " + str(e))


if __name__ == '__main__':
    asyncio.run(main())

