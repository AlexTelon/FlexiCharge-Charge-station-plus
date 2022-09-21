import datetime
from importlib.resources import is_resource
import json
import threading
import time
import websockets
import asyncio
from config import Configurations
from StateHandler import States

class WebSocket():
#THIS FILE IS TO MIMIC THE WEB SOCKET IMPLEMENTATION WITHOUT USING THE WEBSOCKETS 
    my_websocket : websockets = None
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
        pass

    async def get_message(self) -> States:
        pass
                
    async def send_boot_notification(self):
       pass

    # If the idTag has a reservation, start charging from the reservation, set the state to charging,
    # send a response to the central system, start the transaction, set the status to charging, and
    # send a status notification to the central system.
    # :param message: [3, "Unique message id", "RemoteStartTransaction", {"idTag": "12345"}]
    async def remote_start_transaction(self, message):
        pass
    
    async def remote_stop_transaction(self, message):
        pass

    
    async def reserve_now(self, message):
        pass

    
    async def start_transaction(self, is_remote):
       pass

    async def stop_transaction(self, is_remote):
       pass

    
    # Gets no response, is this an error in back-end? Seems to be the case
    async def send_status_notification(self, info):
        pass

        #Depricated in back-end
    async def send_heartbeat(self):
        pass

    
    #Depricated in back-end
    async def send_meter_values(self):
       pass

    
    async def send_data_transfer(self, message_id, message_data):
        pass

    async def recive_data_transfer(self, message):
       pass

    async def send_data_reserve(self):
        pass

    async def send_data_remote_start(self):
        pass

    async def send_data_remote_stop(self):
        pass



    


        