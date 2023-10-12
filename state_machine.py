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
WEBSOCKET = WebSocket()

async def websocketTask():
    WEBSOCKET.start_websocket()
    while True:    
        await asyncio.sleep(1)
        
async def handle_startup_state(state):
    CHARGER_GUI.change_state(state)
    
async def handle_not_available_state(state):
    CHARGER_GUI.change_state(state)

async def handle_available_state(state):
    CHARGER_GUI.generate_qr_code(CHARGER_VARIABLES.charger_id)
    CHARGER_GUI.set_charger_id(CHARGER_VARIABLES.charger_id)
    CHARGER.update_timeout()
    CHARGER_GUI.change_state(state)

async def handle_plug_in_cable_state(state):
    CHARGER_GUI.change_state(state)
    CHARGER.read_via_UART()
    CHARGER_VARIABLES = CHARGER.get_charger_variables()

    if CHARGER.timeout_passed_and_not_connected():
        CHARGER_VARIABLES.reset_variables()
        CHARGER_VARIABLES.current_state = States.S_AVAILABLE
        CHARGER.set_charger_variables(CHARGER_VARIABLES)

    if CHARGER_VARIABLES.is_connected:
        CHARGER_VARIABLES.current_state = States.S_CONNECTING

    WEBSOCKET.set_charger_variables(CHARGER_VARIABLES)

async def handle_connecting_state(state):
    CHARGER_GUI.change_state(state)
    CHARGER.read_via_UART()
    CHARGER_VARIABLES = CHARGER.get_charger_variables()

    if CHARGER.timeout_passed_and_not_connected():
        CHARGER_VARIABLES.reset_variables()
        CHARGER_VARIABLES.current_state = States.S_AVAILABLE
        CHARGER.set_charger_variables(CHARGER_VARIABLES)

    if(CHARGER_VARIABLES.is_connected and CHARGER_VARIABLES.is_charging and CHARGER_VARIABLES.requsted_voltage != ""):
        is_valid_voltage = CHARGER.controll_output_voltage(CHARGER_VARIABLES.requsted_voltage)
        if is_valid_voltage != -1:
            CHARGER_VARIABLES.current_state = States.S_CHARGING
        else:
            CHARGER_VARIABLES.reset_variables()
            CHARGER_VARIABLES.current_state = States.S_AVAILABLE
            CHARGER.set_charger_variables(CHARGER_VARIABLES)

    WEBSOCKET.set_charger_variables(CHARGER_VARIABLES)

async def handle_charging_state(state,charing_start_time):
    CHARGER_GUI.change_state(state)
    CHARGER.read_via_UART()
    CHARGER_VARIABLES = CHARGER.get_charger_variables()

    if not CHARGER.is_connected():
        CHARGER.controll_output_voltage("off")
        await asyncio.gather(WEBSOCKET.stop_transaction(True))
        CHARGER_VARIABLES.reset_variables()

    WEBSOCKET.set_charger_variables(CHARGER_VARIABLES)

    try:
        if (time.time() - charing_start_time) >= 1:
            current = CHARGER.read_current_from_INA219()
            voltage = CHARGER.read_voltage_from_INA219()
            power = CHARGER.calc_power(voltage, (current/1000))
            CHARGER.calc_power_hour(power, 1)
            CHARGER_VARIABLES = CHARGER.get_charger_variables()
            WEBSOCKET.set_charger_variables(CHARGER_VARIABLES)
            await asyncio.gather(WEBSOCKET.send_meter_values())
            charing_start_time = time.time()
    except Exception as e:
        print(str(e))

    CHARGER_GUI.set_charge_precentage(CHARGER_VARIABLES.current_charging_percentage)
    CHARGER_GUI.set_charging_price(CHARGER_VARIABLES.charging_price)
    CHARGER_GUI.set_power_charged(round(CHARGER_VARIABLES.charging_Wh,5))
    CHARGER_GUI.update_charging()    

async def statemachine():
    """
    This function represents the charging station state machine.
    It continuously checks for updates from a WebSocket connection and updates the charging station's state accordingly.
    The code handles various states, such as startup, not available, available, plugin cable, connecting, and charging.
    It also calculates and sends meter values during charging.

    Note: Not all states have been fully implemented; this remains a task for future development.

    """
    charing_start_time = 0
    while True:
        await asyncio.sleep(0.2)
        if(WEBSOCKET != None):
            CHARGER_VARIABLES = WEBSOCKET.get_charger_variables()
            CHARGER.set_charger_variables(CHARGER_VARIABLES)

            state = CHARGER_VARIABLES.current_state 

            if CHARGER_VARIABLES.status == "ReserveNow":
                Reservation.is_reserved, CHARGER_VARIABLES.status,
                Reservation.reservation_id_tag,
                Reservation.reservation_id,
                Reservation.reserved_connector = await WEBSOCKET.get_reservation_info
                
            if state == States.S_STARTUP:
                await handle_startup_state(state)

            elif state == States.S_NOTAVAILABLE:
                await handle_not_available_state(state)

            elif state == States.S_AVAILABLE:
                await handle_available_state(state)

            elif state == States.S_PLUGINCABLE:
                await handle_plug_in_cable_state(state)

            elif state == States.S_CONNECTING:
                await handle_connecting_state(state)

            elif state == States.S_CHARGING:
                await handle_charging_state(state,charing_start_time)            

async def main():
    """
    It initiates a WebSocket-object (from websocket_communication) and runs the state machine
    """
    try:
        statemachine_task = asyncio.create_task(statemachine()) 
        websocket_task = asyncio.create_task(WEBSOCKET.start_websocket())

        await asyncio.gather(statemachine_task, websocket_task)
    except Exception as e:
        print("ERROR: " + str(e))


if __name__ == '__main__':
    asyncio.run(main())

