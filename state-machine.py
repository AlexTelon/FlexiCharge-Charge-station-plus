import PySimpleGUI as sg
import asyncio
import time

from StateHandler import States
from StateHandler import StateHandler
from images import displayStatus

import asyncio
from asyncio.events import get_event_loop
import threading
import websockets
from datetime import datetime
import time
import json
import asyncio
from threading import Thread

state = StateHandler()

class ChargePoint():
    my_websocket = None
    my_id = ""

    reserve_now_timer = 0

    #Define enums for status and error_code (or use the onses in OCPP library)
    status = "Available"
    error_code = "NoError"

    hardcoded_connector_id = 1
    hardcoded_vendor_id = "Flexicharge"

    transaction_id = 123

    #Wont't be used in the final product. It is here until back-end is done with thier implementation (then we know what to send instead)
    id_tag = 123456

    charger_id = 000000

    timestamp_at_last_heartbeat : float = time.perf_counter()
    time_between_heartbeats = 60 * 60 * 24 #In seconds (heartbeat should be sent once every 24h)

    def __init__(self, id, connection):
        self.my_websocket = connection
        self.my_id = id

    async def get_message(self):
        #print("Check messages")
        try:
            msg = await asyncio.wait_for(self.my_websocket.recv(), 1)
            #async for msg in self.my_websocket: #Takes latest message
            print("Check for message")
            message = json.loads(msg)
            print(message)

            if message[2] == "ReserveNow":
                print("ReservNow request recived")
                await asyncio.gather(self.reserve_now(message))
            elif message[2] == "BootNotification":
                if message[3]["status"] == "Accepted":
                    self.charger_id = message[3]["chargerId"] #This is the id number we get from the server (100001)
                    print(self.charger_id)
                    state.set_state(States.S_AVAILABLE)
                else:
                    print("BootNotification error, return from server was: " + message[3]["status"])
            elif message[2] == "RemoteStart":
                await asyncio.gather(self.remote_start_transaction(message[1]))
        except:
            pass


    async def remote_start_transaction(self, unique_message_id):
        msg = [3, 
            unique_message_id, 
            "RemoteStartTransaction", 
            {"status": "Accepted"}
        ]
        response = json.dumps(msg)
        await self.my_websocket.send(response)

    #Will count down every second
    def timer_countdown_reservation(self):
        if self.reserve_now_timer <= 0:
            print("Reservation is up!")
            return
        self.reserve_now_timer = self.reserve_now_timer - 1
        print(self.reserve_now_timer)
        threading.Timer(1, self.timer_countdown_reservation).start()


    async def reserve_now(self, message):
        timestamp = message[3]["expiryDate"]   #Given in ms since epoch
        reserved_for_ms = int(timestamp - (int(time.time()*1000)))
        self.reserve_now_timer = int(reserved_for_ms/100)   #This should be changed to seconds. Time received is too short to test

        threading.Timer(1, self.timer_countdown_reservation).start()

        msg = [3, 
            message[1], #Have to use the unique message id received from server
            "ReserveNow", 
            {"status": "Accepted"}
        ]
        msg_send = json.dumps(msg)
        await self.my_websocket.send(msg_send)
        state.set_state(States.S_FLEXICHARGEAPP)

    async def send_boot_notification(self):
        msg = [2, "0jdsEnnyo2kpCP8FLfHlNpbvQXosR5ZNlh8v", "BootNotification", {
            "chargePointVendor": "AVT-Company",
            "chargePointModel": "AVT-Express",
            "chargePointSerialNumber": "avt.001.13.1",
            "chargeBoxSerialNumber": "avt.001.13.1.01",
            "firmwareVersion": "0.9.87",
            "iccid": "",
            "imsi": "",
            "meterType": "AVT NQC-ACDC",
            "meterSerialNumber": "avt.001.13.1.01" }]
        msg_send = json.dumps(msg)
        await self.my_websocket.send(msg_send)
        await asyncio.sleep(1)

    async def send_data_transfer_req(self):
        msg = [1]
        msg_send = json.dumps(msg)
        await self.my_websocket.send(msg_send)
        #response = await self.my_websocket.recv()
        #print(json.loads(response))
        #await asyncio.sleep(1)

    #Gets no response, is this an error in back-end? Seems to be the case (Update: No response seems to be expected)
    async def send_status_notification(self):
        current_time = datetime.now()
        timestamp = current_time.timestamp() #Can be removed if back-end does want the time-stamp formated
        formated_timestamp = current_time.strftime("%Y-%m-%dT%H:%M:%SZ") #Can be removed if back-end does not want the time-stamp formated
        
        msg = [2, "0jdsEnnyo2kpCP8FLfHlNpbvQXosR5ZNlh8v", "StatusNotification",{
            "connectorId" : self.hardcoded_connector_id,
            "errorCode" : self.error_code,
            "info" : None, #Optional according to official OCPP-documentation
            "status" : self.status,
            "timestamp" : formated_timestamp, #Optional according to official OCPP-documentation
            "vendorId" : self.hardcoded_vendor_id, #Optional according to official OCPP-documentation
            "vendorErrorCode" : None #Optional according to official OCPP-documentation
            }]

        msg_send = json.dumps(msg)
        await self.my_websocket.send(msg_send)
        #No response expected
        #response = await self.my_websocket.recv()
        #print(json.loads(response))

    #Depricated in backend
    async def send_heartbeat(self):
        msg = [2, "0jdsEnnyo2kpCP8FLfHlNpbvQXosR5ZNlh8v", "Heartbeat", {}]
        msg_send = json.dumps(msg)
        await self.my_websocket.send(msg_send)
        #print(await self.my_websocket.recv())
        #await asyncio.sleep(1)
        self.timestamp_at_last_heartbeat = time.perf_counter()

    async def check_if_time_for_heartbeat(self):
        seconds_since_last_heartbeat = time.perf_counter() - (self.timestamp_at_last_heartbeat)
        if seconds_since_last_heartbeat >= self.time_between_heartbeats:
            return True
        else:
            return False

    #Depricated in back-end
    async def send_meter_values(self):
        current_time = datetime.now()
        timestamp = current_time.timestamp() #Can be removed if back-end does want the time-stamp formated
        formated_timestamp = current_time.strftime("%Y-%m-%dT%H:%M:%SZ") #Can be removed if back-end does not want the time-stamp formated

        #Should be replace with "real" sampled values (this is just for testing)
        sample_value = "12345"
        sample_context = "Sample.Clock"
        sample_format = "Raw"
        sample_measurand = "Energy.Active.Export.Register"
        sample_phase = "L1"
        sample_location = "Cable"
        sample_unit = "kWh"

        msg = [2, "0jdsEnnyo2kpCP8FLfHlNpbvQXosR5ZNlh8v", "MeterValues",{
                "connectorId" : self.hardcoded_connector_id,
                "transactionId" : self.transaction_id,
                "meterValue" : [{
                    "timestamp": formated_timestamp,
                    "sampledValue":[
                        {"value" : sample_value,
                        "context" : sample_context,
                        "format" : sample_format,
                        "measurand": sample_measurand,
                        "phase": sample_phase,
                        "location" : sample_location,
                        "unit": sample_unit},
                        ]
                    },],
        }]

        msg_send = json.dumps(msg)
        await self.my_websocket.send(msg_send)
        response = await self.my_websocket.recv()
        print(json.loads(response))
        await asyncio.sleep(1)

    #This is a test function to initiate communication from server side
    async def send_data_transfer_req(self):
        msg = ["chargerplus", "ReserveNow"]
        msg_send = json.dumps(msg)
        await self.my_websocket.send(msg_send)

    #Will need changes when back-end is done!
    async def stop_transaction(self):
        meter_stop = 123
        reason = "Remote"

        current_time = datetime.now()
        timestamp = current_time.timestamp() #Can be removed if back-end does want the time-stamp formated
        formated_timestamp = current_time.strftime("%Y-%m-%dT%H:%M:%SZ") #Can be removed if back-end does not want the time-stamp formated
        
        #Back-end won't use samapled values, instead (I beleave) that they only want the charged level
        sample_value = "12345"
        sample_context = "Sample.Clock"
        sample_format = "Raw"
        sample_measurand = "Energy.Active.Export.Register"
        sample_phase = "L1"
        sample_location = "Cable"
        sample_unit = "kWh"

        msg = [2, "0jdsEnnyo2kpCP8FLfHlNpbvQXosR5ZNlh8v", "StopTransaction",{
                "idTag" : self.id_tag,
                "meterStop" : meter_stop,
                "timestamp" : formated_timestamp,
                "transactionId" : self.transaction_id,
                "reason" : reason,
                "transactionData" : [{
                    "timestamp": formated_timestamp,
                    "sampledValue":[
                        {"value" : sample_value,
                        "context" : sample_context,
                        "format" : sample_format,
                        "measurand": sample_measurand,
                        "phase": sample_phase,
                        "location" : sample_location,
                        "unit": sample_unit},
                        ]
                    },],
        }]

        msg_send = json.dumps(msg)
        await self.my_websocket.send(msg_send)
        response = await self.my_websocket.recv()
        response_parsed = json.loads(response)
        stop_status = response_parsed[3]['status']
        print("Stap status: " + stop_status)
        await asyncio.sleep(1)

def GUI():
    sg.theme('black')

    startingUpLayout =      [
                                [
                                    sg.Image(data=displayStatus.startingUp(), key='IMAGE', pad = ((0,0),(0,0)), size=(480, 800))  
                                ]       
                            ]

    chargingPercentLayout = [
                                [
                                    sg.Text("0", font=('ITC Avant Garde Std Md', 160), key='PERCENT', text_color='Yellow')
                                ]
                            ]
   
    chargingPercentMarkLayout = [
                                    [
                                        sg.Text("%", font=('ITC Avant Garde Std Md', 55), key='PERCENTMARK', text_color='Yellow')
                                    ]
                                ]

    chargingPowerLayout =   [
                                [  
                                    sg.Text("61 kW at 7.3kWh", font=('Lato', 20), key='POWER', justification='center', text_color='white')
                                ]
                            ]

    chargingTimeLayout =   [
                                [  
                                    sg.Text("4 minutes until full", font=('Lato', 20), key='TIME', justification='center', text_color='white')
                                ]
                            ]
    chargingPriceLayout =   [
                                [  
                                    sg.Text("4.5 SEK per KWH", font=('Lato', 20), key='PRICE', justification='center', text_color='white')
                                ]
                            ]

    background_Window = sg.Window(title="FlexiCharge", layout=startingUpLayout, no_titlebar=True, location=(0,0), size=(480, 800), keep_on_top=False).Finalize()
    background_Window.TKroot["cursor"] = "none"

    chargingPercent_window = sg.Window(title="FlexiChargeChargingPercentWindow", layout=chargingPercentLayout, location=(140, 245), grab_anywhere=False, no_titlebar=True, background_color='black', margins=(0,0)).finalize()
    chargingPercent_window.TKroot["cursor"] = "none"
    chargingPercent_window.hide()

    chargingPercentMark_window = sg.Window(title="FlexiChargeChargingPercentWindow", layout=chargingPercentMarkLayout, location=(276, 350), grab_anywhere=False, no_titlebar=True, background_color='black', margins=(0,0)).finalize()
    chargingPercentMark_window.TKroot["cursor"] = "none"
    chargingPercentMark_window.hide()

    chargingPower_window = sg.Window(title="FlexiChargeChargingPowerWindow", layout=chargingPowerLayout, location=(162, 645), grab_anywhere=False, no_titlebar=True, background_color='black', margins=(0,0)).finalize()
    chargingPower_window.TKroot["cursor"] = "none"
    chargingPower_window.hide()

    chargingTime_window = sg.Window(title="FlexiChargeChargingTimeWindow", layout=chargingTimeLayout, location=(162, 694), grab_anywhere=False, no_titlebar=True, background_color='black', margins=(0,0)).finalize()
    chargingTime_window.TKroot["cursor"] = "none"
    chargingTime_window.hide()

    chargingPrice_window = sg.Window(title="FlexiChargeChargingTimeWindow", layout=chargingPriceLayout, location=(125, 525), grab_anywhere=False, no_titlebar=True, background_color='black', margins=(0,0)).finalize()
    chargingPrice_window.TKroot["cursor"] = "none"
    chargingPrice_window.hide()

    return background_Window, chargingPercent_window, chargingPercentMark_window, chargingTime_window, chargingPower_window, chargingPrice_window

window_back, window_chargingPercent, window_chargingPercentMark, window_chargingPower, window_chargingTime, window_chargingPrice = GUI()

#update all the windows
def refreshWindows():
    global window_back, window_chargingPower, window_chargingTime, window_chargingPercent, window_chargingPrice
    window_back.refresh()
    window_chargingPower.refresh()
    window_chargingTime.refresh()
    window_chargingPercent.refresh()
    window_chargingPercentMark.refresh()
    window_chargingPrice.refresh()

async def statemachine(chargePoint):

    await chargePoint.get_message()

    global window_back

    chargerID = chargePoint.charger_id
    
    firstNumberOfChargerID = int(chargerID % 10) 
    secondNumberOfChargerID = int(chargerID/10) % 10 
    thirdNumberOfChargerID = int(chargerID/100) % 10  
    fouthNumberOfChargerID = int(chargerID/1000) % 10 
    fifthNumberOfChargerID = int(chargerID/10000) % 10 
    sixthNumberOfChargerID = int(chargerID/100000) % 10 
    
    chargerIdLayout =    [
                    [   
                        sg.Text(firstNumberOfChargerID, font=('Tw Cen MT Condensed Extra Bold', 30), key='ID0', justification='center', pad=(20,0)),
                        sg.Text(secondNumberOfChargerID, font=('Tw Cen MT Condensed Extra Bold', 30), key='ID1', justification='center', pad=(25,0)),
                        sg.Text(thirdNumberOfChargerID, font=('Tw Cen MT Condensed Extra Bold', 30), key='ID2', justification='center', pad=(20,0)),
                        sg.Text(fouthNumberOfChargerID, font=('Tw Cen MT Condensed Extra Bold', 30), key='ID3', justification='center', pad=(25,0)),
                        sg.Text(fifthNumberOfChargerID, font=('Tw Cen MT Condensed Extra Bold', 30), key='ID4', justification='center', pad=(20,0)),
                        sg.Text(sixthNumberOfChargerID, font=('Tw Cen MT Condensed Extra Bold', 30), key='ID5', justification='center', pad=(25,0))
                    ]
                ]

    chargerID_window = sg.Window(title="FlexiChargeTopWindow", layout=chargerIdLayout, location=(20,700),keep_on_top=True, grab_anywhere=False, transparent_color=sg.theme_background_color(), no_titlebar=True).finalize()
    chargerID_window.TKroot["cursor"] = "none"
    chargerID_window.hide()

    while True:
        await asyncio.gather(chargePoint.get_message())
        
        if state.get_state() == States.S_AVAILABLE:
            #Display QR code image
            window_back['IMAGE'].update(data=displayStatus.qrCode())
            #Show Charger id on screen with QR code image
            chargerID_window.UnHide()
            #update the window
            refreshWindows()   
        elif state.get_state() == States.S_FLEXICHARGEAPP:
            window_back['IMAGE'].update(data=displayStatus.flexiChargeApp())
            #Hide the charge id on this state
            chargerID_window.Hide()
            refreshWindows()  
        elif state.get_state() == States.S_PLUGINCABLE:

            window_back['IMAGE'].update(data=displayStatus.plugCable())
            #Hide the charge id on this state
            chargerID_window.Hide()
            refreshWindows()  

        elif state.get_state() == States.S_CONNECTING:
            chargerID_window.hide()
            window_back['IMAGE'].update(data=displayStatus.connectingToCar())
            refreshWindows() 

        elif state.get_state() == States.S_CHARGING:

            window_back['IMAGE'].update(data=displayStatus.charging())

            #Display all the windows below during charging image shown on screen
            window_chargingPercent.un_hide()
            window_chargingPercentMark.un_hide()
            window_chargingTime.un_hide()
            window_chargingPower.un_hide()
            window_chargingPrice.un_hide()

            percent = 0
            while True:

                if percent >= 10:
                    #move charging percent on screen when percent >= 10
                    window_chargingPercent.move(60, 245)
                    #move the charging mark (%) on screen
                    window_chargingPercentMark.move(330, 350)                     
                if percent > 10:
                    break

                refreshWindows()
                time.sleep(1)
                percent = percent + 1
                #update in precents how full the battery currently is 
                window_chargingPercent['PERCENT'].update(str(percent))

        elif state.get_state() == States.S_BATTERYFULL:

            #hide all the windows below during barttery full image shown on screen
            window_chargingPercent.hide()
            window_chargingPercentMark.hide()
            window_chargingTime.hide()
            window_chargingPower.hide()
            window_chargingPrice.hide()

            window_back['IMAGE'].update(data=displayStatus.batteryFull())
            refreshWindows()

async def main():
    try:
        async with websockets.connect(
        'ws://54.220.194.65:1337/chargerplus',
         subprotocols=['ocpp1.6']
        ) as ws:
            chargePoint = ChargePoint("chargerplus", ws)

            await chargePoint.send_boot_notification()
            #await chargePoint.send_heartbeat()
            asyncio.get_event_loop().run_until_complete(await statemachine(chargePoint))
    except:
        print("Websocket error: Could not connect to server!")
        #Ugly? Yes! Works? Yes! (Should might use the statemachine but that will generate problems due to the websocket not working, due to the lack of time i won't fix that now)
        while True:
            state.set_state(States.S_NOTAVAILABLE)
            global window_back
            #Display QR code image
            window_back['IMAGE'].update(data=displayStatus.chargeNotAvailable())
            #update the window
            refreshWindows()

if __name__ == '__main__':
    asyncio.run(main())
