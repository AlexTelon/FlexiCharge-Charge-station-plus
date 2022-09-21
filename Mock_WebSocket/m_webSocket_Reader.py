import datetime
from importlib.resources import is_resource
import json
import threading
import time
import websockets
import asyncio
from StateHandler import States
from config import Configurations

class WebSocket():
#FUNCTIONS AND VARIABLES ARE RELEVANT TO WEB SOCKETS. THIS FILE IS TO EVALUATE HOW WEBSOCKET
#IS TO BE USED 


    def __init__(self, id, connection):
        pass

    async def get_message(self) -> States:
        return States.S_AVAILABLE
    
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