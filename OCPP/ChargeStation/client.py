#Todo - Implement authorization cache (Not requirement)
#     - Implement authorization list (Might not be priority or required in this project)


import asyncio
import websockets
from datetime import datetime

from ocpp.routing import on
from ocpp.v16 import call, ChargePoint as cp, call_result
from ocpp.v16.enums import Action, AuthorizationStatus, DataTransferStatus, RegistrationStatus, RemoteStartStopStatus


class ChargePoint(cp):
    hardcoded_id_tag = "MyID"
    hardcoded_vendor_id = "vendorID"
    hardcoded_connector_id = 123
    hardcoded_meter_start = 10
    hardcoded_reservation_id = 1
    

    async def send_boot_notification(self):
        request = call.BootNotificationPayload(
            charge_point_model="Model",
            charge_point_vendor="FlexiCharge"
        )

        response = await self.call(request)

        if response.status ==  RegistrationStatus.accepted:
            print("Connected to central system.")

    async def send_authorization(self):
        request = call.AuthorizePayload(
            #This is the ID we send to the server. Hardcoded for now. Replace with the id from the tag.
            id_tag = self.hardcoded_id_tag
        )
        #Returns an object containing a single Dictionary (Dict)
        response = await self.call(request)
        
        #id_tag_info is the name of the dictionary and status is the member (named in chargepoint.py -> onAuthorize)
        if response.id_tag_info["status"] ==  AuthorizationStatus.accepted:
            print("Authorized.")
 

    async def send_start_transaction(self):
        #Todo - Make all values have meaning
        #     - Update authorization cache
        request = call.StartTransactionPayload(
            connector_id = self.hardcoded_connector_id,
            id_tag = self.hardcoded_id_tag,
            meter_start = self.hardcoded_meter_start,
            reservation_id = self.hardcoded_reservation_id,
            timestamp = datetime.utcnow().isoformat()
        )

        response = await self.call(request)

        if response.id_tag_info["status"] == AuthorizationStatus.accepted:
            print("Charge start")
        elif response.id_tag_info["status"] == AuthorizationStatus.blocked:
            print("Blocked. No charge started")






#Two functions that are not finished or tested
    #NOT TESTED.
    async def send_data_transfer_req(self, vendor_id:str, message_id:str, data:str):
        print("Sending data transfer req")
        request = call.DataTransferPayload(
            vendor_id= self.hardcoded_vendor_id
        )
        
        response = await self.call(request)

        if response.status == DataTransferStatus.accepted:
            print("Data sent successfully")
        elif response.status == DataTransferStatus.rejected:
            #Todo: Implement 
            print("Data declined")
    #NOT FINISHED. ON HOLD.
    @on(Action.RemoteStartTransaction)
    async def remote_start_transaction(self, id_tag:str, connectorID:str="", chargingProfile:str=""):
        print("Remote start transaction called from central system")

        if self.authorize_remote_tx_requests == True:
            if self.can_start_charge == True:
                self.can_start_charge = False

                response = self.send_authorization()
                response = await response
                asyncio.ensure_future(response)
                await response

                result = RemoteStartStopStatus.accepted
            elif self.can_start_charge == False:
                result = RemoteStartStopStatus.rejected
        
        return call_result.RemoteStartTransactionPayload(
            status = result
        )






#This is a coroutine running in paralell with other coroutines
async def user_input_task(cp):
    while 1:
        a = input(">> ")
        if a == "1":
            await asyncio.gather(cp.send_boot_notification())
        elif a == "2":
            await asyncio.gather(cp.send_authorization())
        elif a == "5":
            await asyncio.gather(cp.send_start_transaction())
        elif a == "9":
            #To pass on input. Needed when server is sending information
            await asyncio.sleep(2)


async def main():
    async with websockets.connect(
        'ws://localhost:9000/CP_1',
        #'ws://54.220.194.65:1337/abc123',
         subprotocols=['ocpp1.6']
    ) as ws:

        cp = ChargePoint('abc123', ws)

        #, cp.send_boot_notification())   #start() will keep program from continuing
        await asyncio.gather(cp.start(), user_input_task(cp))

if __name__ == '__main__':
    asyncio.run(main())