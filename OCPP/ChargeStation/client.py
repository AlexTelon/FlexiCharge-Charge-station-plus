import asyncio
from time import time
from typing import Dict
import websockets
import datetime
from threading import Thread
from ocpp.v16 import call, ChargePoint as cp
from ocpp.v16.enums import AuthorizationStatus, RegistrationStatus
#import _thread
#import nest_asyncio

class ChargePoint(cp):
    async def send_boot_notification(self):
        request = call.BootNotificationPayload(
            charge_point_model="Optimus",
            charge_point_vendor="The Mobility House"
        )

        response = await self.call(request)

        if response.status ==  RegistrationStatus.accepted:
            print("Connected to central system.")

    async def send_authorization(self):
        request = call.AuthorizePayload(
            id_tag = "MyID" #This is the ID we send to the server. Hardcoded for now. Replace with the id from the tag.
        )

        response = await self.call(request) #Returns an object containing a single Dictionary (Dict)
        
        #id_tag_info is the name of the dictionary and status is the member (named in chargepoint.py -> onAuthorize)
        if response.id_tag_info["status"] ==  AuthorizationStatus.accepted:
            print("Authorized.")

    #Sends a heartbeat to Centralstation, print the result from Centralstation
    #TODO According to OCPP-documentation, Chargepoint internal clock should be synced with Centralstation's clock (which the heartbeat response contains).
    #Will add this when correct time is needed for our Chargepoint!
    async def on_heartbeat(self):
        request = call.HeartbeatPayload()
        response = await self.call(request)

        print("Heartbeat: " + str(response))

    #Sends a heartbeat to Centralstation periodically
    async def generate_periodic_heartbeat(self, interval):
        while 1:
            await self.on_heartbeat()
            await asyncio.sleep(interval)

#This is a coroutine running in paralell with other coroutines
async def user_input_task(cp):
    a = 0
    while 1:
        #a = input(">> ")
        if a == 0:
            print("Testing 1")
            await asyncio.gather(cp.send_boot_notification())
        elif a == 1:
            print("Testing 2")
            await asyncio.gather(cp.send_authorization())
        elif a == 2:
            print("Testing 3")
            await asyncio.gather(cp.on_heartbeat())
        await asyncio.sleep(5)
        a = (a + 1) % 3

async def main():
    async with websockets.connect(
        'ws://localhost:9000/CP_1',
         subprotocols=['ocpp1.6']
    ) as ws:

        cp = ChargePoint('CP_1', ws)
        asyncio.gather(cp.generate_periodic_heartbeat(1))
        await asyncio.gather(cp.start(), user_input_task(cp))   #start() will keep program from continuing

if __name__ == '__main__':
    asyncio.run(main())
