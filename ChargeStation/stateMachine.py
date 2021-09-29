from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from _typeshed import Self

import asyncio
from os import stat
from tkinter import font
import websockets
import json
import time
import multiprocessing
import io
import PySimpleGUI as sg
import platform
import time
from StateHandler import States
from StateHandler import StateHandler

from PIL import Image, ImageTk
from multiprocessing import Process

from images import displayStatus

from datetime import datetime

from ocpp.routing import on, after
from ocpp.v16 import ChargePoint as cp
from ocpp.v16.enums import Action, RegistrationStatus, AuthorizationStatus, DataTransferStatus, ChargePointStatus, RemoteStartStopStatus
from ocpp.v16 import call_result, call
#from client import ChargePoint

class ChargePoint(cp):
    hardcoded_id_tag = "MyID"
    hardcoded_vendor_id = "vendorID"
    hardcoded_connector_id = 123
    hardcoded_meter_start = 10
    hardcoded_reservation_id = 1
    
    def __init__(self, _id, connection):
        cp.__init__(self,  _id, connection)
        self.status = ChargePointStatus.available
        self.transaction_id = None

    async def send_boot_notification(self):
        request = call.BootNotificationPayload(
            charge_point_model="Model",
            charge_point_vendor="FlexiCharge"
        )

        response = await self.call(request)

        if response.status ==  RegistrationStatus.accepted:
            print("Connected to central system.")
            print("send_boot_notification response from CentralStation: " + str(response))
        
        return response


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

    #Sends a heartbeat to Centralstation, print the result from Centralstation
    #####TODO According to OCPP-documentation, Chargepoint internal clock should be synced with Centralstation's clock (which the heartbeat response contains).
    #####Will add this when correct time is needed for our Chargepoint!
    async def on_heartbeat(self):
        request = call.HeartbeatPayload()
        response = await self.call(request)
        print("Heartbeat: " + str(response))

    #Sends a heartbeat to Centralstation periodically
    async def generate_periodic_heartbeat(self, interval):
        while 1:
            await self.on_heartbeat()
            await asyncio.sleep(interval)

    #Sets status to charging after transaction has been started. Here we would also like to update the screen when such functionality is implemented!
    @after(Action.StartTransaction)
    def after_start_transaction(self):
        self.status = ChargePointStatus.charging
        print("Transaction status is set to: " + self.status)

    async def send_stop_transaction(self, transaction_id:int):
        request =call.StopTransactionPayload
        transaction_id != self.transaction_id
            
        response = await self.call(request)
         
        if response.id_tag_info["status"] == AuthorizationStatus.invalid:
            print("Charger {self.id}: Stopping transaction")

state = StateHandler()

def GUI():
    sg.theme('Black')

    layout1 =    [
                    [
                        sg.Text(" ")
                    ],
                    [
                        sg.Image(data=displayStatus.startingUp(), key='IMAGE', size=(480, 800))
                        
                    ]
                ]

    window = sg.Window(title="FlexiCharge", layout=layout1, no_titlebar=True, location=(0,0), size=(480,800), keep_on_top=False).Finalize()
    window.TKroot["cursor"] = "none"
    screen = 0

    return window


async def statemachine(ocpp_client):
    window = GUI()
    global state

    response = await ocpp_client.send_boot_notification()
    chargerID = response.charger_id

    firstNumberOfChargerID = int(chargerID % 10) 
    secondNumberOfChargerID = int(chargerID/10) % 10 
    thirdNumberOfChargerID = int(chargerID/100) % 10  
    fouthNumberOfChargerID = int(chargerID/1000) % 10 
    fifthNumberOfChargerID = int(chargerID/10000) % 10 
    sixthNumberOfChargerID = int(chargerID/100000) % 10

    layout = [
                [   
                     sg.Text(firstNumberOfChargerID, font=('Tw Cen MT Condensed Extra Bold', 30), key='ID0', justification='center', pad=(15,0)),
                     sg.Text(secondNumberOfChargerID, font=('Tw Cen MT Condensed Extra Bold', 30), key='ID1', justification='center', pad=(25,0)),
                     sg.Text(thirdNumberOfChargerID, font=('Tw Cen MT Condensed Extra Bold', 30), key='ID2', justification='center', pad=(20,0)),
                     sg.Text(fouthNumberOfChargerID, font=('Tw Cen MT Condensed Extra Bold', 30), key='ID3', justification='center', pad=(25,0)),
                     sg.Text(fifthNumberOfChargerID, font=('Tw Cen MT Condensed Extra Bold', 30), key='ID4', justification='center', pad=(20,0)),
                     sg.Text(sixthNumberOfChargerID, font=('Tw Cen MT Condensed Extra Bold', 30), key='ID5', justification='center', pad=(25,0))
                ]
            ]

    top_window = sg.Window(title="FlexiChargeTopWindow", layout=layout, location=(18,720), keep_on_top=True, grab_anywhere=False, transparent_color=sg.theme_background_color(), no_titlebar=True).finalize()
    top_window.TKroot["cursor"] = "none"
    top_window.hide()

    while True:

        if state.get_state() == States.S_STARTUP:
            time.sleep(5)
            state.set_state(States.S_NOTAVAILABLE)
            window['IMAGE'].update(data=displayStatus.chargeNotAvailable())
            window.refresh()
            time.sleep(5)

            if(response.status ==  RegistrationStatus.accepted):
                state.set_state(States.S_AVAILABLE)
                window['IMAGE'].update(data=displayStatus.qrCode())
                top_window.UnHide()
                window.refresh()
            else:
                state.set_state(States.S_NOTAVAILABLE)
                window['IMAGE'].update(data=displayStatus.chargeNotAvailable())
                top_window.hide()
                window.refresh()

            time.sleep(2)

async def main():
    #asyncio.get_event_loop().run_until_complete(statemachine(ocpp_client))
    async with websockets.connect(
        #0'ws://localhost:9000/CP_1',
        'ws://54.220.194.65:1337/123abc',
         subprotocols=['ocpp1.6']
    ) as ws:
        ocpp_client = ChargePoint('abc123', ws)
        #cp = ChargePoint('abc123', ws)
        await asyncio.gather(ocpp_client.start(), statemachine(ocpp_client))
        #asyncio.gather(cp.generate_periodic_heartbeat(1))
        #await asyncio.gather(cp.start(), user_input_task(cp))   #start() will keep program from continuing


if __name__ == '__main__':
    asyncio.run(main())