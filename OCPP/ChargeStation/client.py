import asyncio
from typing import Dict
import websockets

from ocpp.v16 import call, ChargePoint as cp
from ocpp.v16.enums import AuthorizationStatus, RegistrationStatus


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


#This is a coroutine running in paralell with other coroutines
async def user_input_task(cp):
    while 1:
        a = input(">> ")
        if a == "1":
            await asyncio.gather(cp.send_boot_notification())
        elif a == "2":
            await asyncio.gather(cp.send_authorization())


async def main():
    async with websockets.connect(
        'ws://localhost:9000/CP_1',
         subprotocols=['ocpp1.6']
    ) as ws:

        cp = ChargePoint('CP_1', ws)

        await asyncio.gather(cp.start(), user_input_task(cp))#, cp.send_boot_notification())   #start() will keep program from continuing


if __name__ == '__main__':
    asyncio.run(main())