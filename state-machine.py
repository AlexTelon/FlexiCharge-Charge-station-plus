import PySimpleGUI as sg
import asyncio
import time

from StateHandler import States
from StateHandler import StateHandler
from images import displayStatus

import  qrcode

import asyncio
from asyncio.events import get_event_loop
from asyncio.tasks import gather
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

    meter_value_total = 0   #Send this to server at start and stop. It will calculate cost. Incremented during charging.
    current_charging_percentage = 0

    #Reservation related variables
    reserve_now_timer = 0
    is_reserved = False
    reservation_id_tag = None
    reservation_id = None
    reserved_connector = None
    ReserveConnectorZeroSupported = True

    #Transaction related variables
    is_charging = False
    charging_id_tag = None
    charging_connector = None
    charging_Wh = 0 #I think this is how many Wh have been used to charge
    transaction_id = None

    #Define enums for status and error_code (or use the onses in OCPP library)
    status = "Available"
    error_code = "NoError"

    hardcoded_connector_id = 1
    hardcoded_vendor_id = "com.flexicharge"

    hardcoded_id_tag = 1

    charger_id = 00000

    timestamp_at_last_heartbeat : float = time.perf_counter()
    time_between_heartbeats = 60 * 60 * 24 #In seconds (heartbeat should be sent once every 24h)


    def __init__(self, id, connection):
        self.my_websocket = connection
        self.my_id = id

    async def get_message(self):
        c = 0
        while c < 3:
            c = c + 1
            try:
                msg = await asyncio.wait_for(self.my_websocket.recv(), 0.1)
                #async for msg in self.my_websocket: #Takes latest message
                print("Check for message")
                message = json.loads(msg)
                print(message)

                if message[2] == "ReserveNow":
                    await asyncio.gather(self.reserve_now(message))
                elif message[2] == "BootNotification":
                    message_str = str(message[3]["status"])
                    if message_str == "Accepted":
                        self.status = "Available"
                        state.set_state(States.S_AVAILABLE)
                        await asyncio.gather(self.send_status_notification(None)) #Status notification should be sent after a boot
                    else:
                        self.status = "Faulted"
                        await asyncio.gather(self.send_status_notification(None))
                        state.set_state(States.S_NOTAVAILABLE)
                elif message[2] == "RemoteStartTransaction":
                    await asyncio.gather(self.remote_start_transaction(message))
                elif message[2] == "RemoteStopTransaction":
                    await asyncio.gather(self.remote_stop_transaction(message))
                elif message[2] == "DataTransfer":
                    await asyncio.gather(self.recive_data_transfer(message))
                elif message[2] == "StartTransaction":
                    #self.transaction_id = message[3]["transactionId"]    #Store transaction id from server
                    self.transaction_id = 347
            except:
                pass

    #AuthorizeRemoteTxRequests is always false since no authorize function exists in backend(?)
    #TODO - Change when multiple connectors exists. Add parent id tag.
    #       No handling for connectorID = 0 since only a single connector will exist in mvp
    #       No status_notification is sent since it does not get a response and locks the program
    async def remote_start_transaction(self, message):
        if int(message[3]["idTag"]) == self.reservation_id_tag: #If the idTag has a reservation
            self.start_charging_from_reservation()
            print("Remote transaction started")
            state.set_state(States.S_CHARGING)
            msg = [3, 
                message[1], #Unique message id
                "RemoteStartTransaction", 
                {"status": "Accepted"}
            ]
            response = json.dumps(msg)
            await self.my_websocket.send(response)

            await self.start_transaction(is_remote=True)
            self.status = "Charging"
            await self.send_status_notification(None)   #Notify central system that connector is now available
            print("Charge should be started")
        else:   #A non reserved tag tries to use the connector
            print("This tag does not have a reservation")
            msg = [3, 
                message[1], #Unique message id
                "RemoteStartTransaction", 
                {"status": "Rejected"}
            ]
            response = json.dumps(msg)
            await self.my_websocket.send(response)

    async def remote_stop_transaction(self, message):
        local_transaction_id = message[3]["transactionID"]
        if self.is_charging == True: #and int(local_transaction_id) == int(self.transaction_id):
            print("Remote stop charging")
            msg = [3, 
                message[1], #Have to use the unique message id received from server
                "RemoteStopTransaction", 
                {"status": "Accepted"}
            ]
            msg_send = json.dumps(msg)
            await self.my_websocket.send(msg_send)
            await self.stop_transaction(is_remote=True) #Stop transaction and inform server
        else:
            print("Charging cannot be stopped")
            msg = [3, 
                message[1], #Have to use the unique message id received from server
                "RemoteStopTransaction", 
                {"status": "Rejected"}
            ]
            msg_send = json.dumps(msg)
            await self.my_websocket.send(msg_send)

    #Will count down every second
    def timer_countdown_reservation(self):
        if self.reserve_now_timer <= 0:
            print("Reservation is canceled!")
            self.hard_reset_reservation()
            self.status = "Available"
            asyncio.run(self.send_status_notification(None)) #Notify back-end that we are availiable again
            return
        self.reserve_now_timer = self.reserve_now_timer - 1
        #Should only countdown if status us Reserved, otherwise won't be able to start charging
        if self.status == "Reserved":
            threading.Timer(1, self.timer_countdown_reservation).start()    #Countdown every second
##########################################################################################################################
    def meter_counter_charging(self):
        if self.is_charging == True:
            self.meter_value_total = self.meter_value_total + 1
            self.current_charging_percentage = self.current_charging_percentage + 1
            asyncio.run(self.send_data_transfer(1, self.current_charging_percentage))
            threading.Timer(3, self.meter_counter_charging).start()
        else:
            print("{}{}".format("Total charge: ", self.meter_value_total))

    
    def hard_reset_reservation(self):
        self.is_reserved = False
        self.reserve_now_timer = 0
        self.reservation_id_tag = None
        self.reservation_id = None
        print("Hard reset reservation")

    def hard_reset_charging(self):
        self.is_charging = False
        self.charging_id_tag = None
        self.charging_connector = None
        print("Hard reset charging")
    
    def start_charging_from_reservation(self):
        self.is_charging = True
        self.charging_id_tag = self.reservation_id_tag
        self.charging_connector = self.reserved_connector
        #threading.Timer(1, self.meter_counter_charging).start()
        #threading.Timer(2, self.send_periodic_meter_values).start()

    def send_periodic_meter_values(self):
        asyncio.run(self.send_data_transfer(1, self.current_charging_percentage))
        if self.is_charging:
            threading.Timer(2, self.send_periodic_meter_values).start()

    def start_charging(self, connector_id, id_tag):
        self.is_charging = True
        self.charging_id_tag = id_tag
        self.charging_connector = connector_id
        threading.Timer(1, self.meter_counter_charging).start()

    async def reserve_now(self, message):
        local_reservation_id = message[3]["reservationID"]
        local_connector_id = message[3]["connectorID"]
        if self.reservation_id == None or self.reservation_id == local_reservation_id:
            if self.ReserveConnectorZeroSupported == False and local_connector_id == 0:
                print("Connector zero not allowed")
                msg = [3, 
                    message[1], #Have to use the unique message id received from server
                    "ReserveNow", 
                    {"status": "Rejected"}
                ]
                msg_send = json.dumps(msg)
                await self.my_websocket.send(msg_send)
                return
            self.hard_reset_reservation()
            self.is_reserved = True
            self.status = "Reserved"
            await asyncio.gather(self.send_status_notification(None))
            state.set_state(States.S_FLEXICHARGEAPP)
            self.reservation_id_tag = int(message[3]["idTag"])
            self.reservation_id = message[3]["reservationID"]
            self.reserved_connector = message[3]["connectorID"]
            timestamp = message[3]["expiryDate"]   #Given in ms since epoch
            reserved_for_s = int(timestamp - int(time.time()))
            self.reserve_now_timer = int(reserved_for_s)#reserved_for_ms/1000)   #Reservation time in seconds
            self.timer_countdown_reservation  #Countdown every second

            msg = [3, 
                message[1], #Have to use the unique message id received from server
                "ReserveNow", 
                {"status": "Accepted"}
            ]
            msg_send = json.dumps(msg)
            await self.my_websocket.send(msg_send)

        elif self.reserved_connector == local_connector_id:
            print("Connector occupied")
            msg = [3, 
                message[1], #Have to use the unique message id received from server
                "ReserveNow", 
                {"status": "Occupied"}
            ]
            msg_send = json.dumps(msg)
            await self.my_websocket.send(msg_send)
        else:
            print("Implement other messages for non accepted reservations")
            msg = [3, 
                message[1], #Have to use the unique message id received from server
                "ReserveNow", 
                {"status": "Occupied"}
            ]
            msg_send = json.dumps(msg)
            await self.my_websocket.send(msg_send)
###################################################################################################################
    #Tells server we have started a transaction (charging)
    async def start_transaction(self, is_remote):
        current_time = datetime.now()
        timestamp = current_time.timestamp()

        if is_remote == True:
            #If remote then charging have started in remote_start_transaction. Notify server here.
            msg = [2, "0jdsEnnyo2kpCP8FLfHlNpbvQXosR5ZNlh8v", "StartTransaction", {
            "connectorId" : self.charging_connector,
            "id_tag": self.charging_id_tag,
            "meterStart":self.meter_value_total,
            "timestamp" : timestamp,
            "reservationId": self.reservation_id,
             }]
        
            self.hard_reset_reservation()
            msg_send = json.dumps(msg)
            await self.my_websocket.send(msg_send)
        else:   #No reservation
            self.start_charging(self.hardcoded_connector_id, self.hardcoded_id_tag)

            msg = [2, "0jdsEnnyo2kpCP8FLfHlNpbvQXosR5ZNlh8v", "StartTransaction", {
            "connectorId" : self.charging_connector,
            "id_tag": self.charging_id_tag ,
            "meterStart":self.meter_value_total,
            "timestamp" : timestamp,
            "reservationId": None,  #If here, no reservation was made
             }]

            msg_send = json.dumps(msg)
            await self.my_websocket.send(msg_send)

    #TODO - Adjust to multiple connectors when added. Assumes a single connector
    async def stop_transaction(self, is_remote):
        current_time = datetime.now()
        timestamp = current_time.timestamp()
        self.status = "Available"
        await asyncio.gather(self.send_status_notification(None))
        if is_remote == True:
            msg = [2, "0jdsEnnyo2kpCP8FLfHlNpbvQXosR5ZNlh8v", "StopTransaction", {
                "idTag": self.charging_id_tag,
                "meterStop": self.meter_value_total,
                "timestamp": timestamp,
                "transactionId": self.transaction_id,
                "reason": "Remote",
                "transactionData": None#[
                    #{
                    #Can place timestamp here. (Optional)
                    #},
                    #Can place meterValues here. (Optional)
                #]
                }]
            msg_send = json.dumps(msg)
            await self.my_websocket.send(msg_send)
            self.hard_reset_charging()
        else:
            msg = [2, "0jdsEnnyo2kpCP8FLfHlNpbvQXosR5ZNlh8v", "StopTransaction", {
                "idTag": self.charging_id_tag,
                "meterStop": self.meter_value_total,
                "timestamp": timestamp,
                "transactionId": self.transaction_id,
                "reason": "Remote",
                "transactionData": None#[
                    #{
                    #Can place timestamp here. (Optional)
                    #},
                    #Can place meterValues here. (Optional)
                #]
                }]
            msg_send = json.dumps(msg)
            await self.my_websocket.send(msg_send)
            self.hard_reset_charging()

        response = await self.my_websocket.recv()
        print(json.loads(response))

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

    #Gets no response, is this an error in back-end? Seems to be the case
    async def send_status_notification(self, info):
        current_time = datetime.now()
        timestamp = current_time.timestamp() #Can be removed if back-end does want the time-stamp formated
        formated_timestamp = current_time.strftime("%Y-%m-%dT%H:%M:%SZ") #Can be removed if back-end does not want the time-stamp formated
        
        msg = [2, "0jdsEnnyo2kpCP8FLfHlNpbvQXosR5ZNlh8v", "StatusNotification",{
            "connectorId" : self.hardcoded_connector_id,
            "errorCode" : self.error_code,
            "info" : info, #Optional according to official OCPP-documentation
            "status" : self.status,
            "timestamp" : timestamp, #Optional according to official OCPP-documentation
            "vendorId" : self.hardcoded_vendor_id, #Optional according to official OCPP-documentation
            "vendorErrorCode" : "None" #Optional according to official OCPP-documentation
            }]

        msg_send = json.dumps(msg)
        await self.my_websocket.send(msg_send)
        print("Status notification sent with message: ")
        print(msg)
        self.timestamp_at_last_status_notification = time.perf_counter()

    #Depricated in back-end
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
###########################################################################################################
    async def send_data_transfer(self, message_id, message_data):
        s:str = "{}{}{}{}{}{}{}".format("{\"transactionId\":", self.transaction_id, ",\"latestMeterValue\":", message_data, ",\"CurrentChargePercentage\":", message_data, "}")
        print(s)

        msg = [2, "0jdsEnnyo2kpCP8FLfHlNpbvQXosR5ZNlh8v", "DataTransfer",{
                #"vendorId" : self.hardcoded_vendor_id,
                "messageId" : "ChargeLevelUpdate",
                "data" : s
        }]

        msg_send = json.dumps(msg)
        await self.my_websocket.send(msg_send)

    async def recive_data_transfer(self, message):
        status = "Rejected"
        if message[3]["vendorId"] == self.hardcoded_vendor_id:
            if message[3]["messageId"] == "BootData":
                parsed_data = json.loads(message[3]["data"])
                self.charger_id = parsed_data["chargerId"]
                print("Charger ID is set to: " + str(self.charger_id))
                status = "Accepted"
            else:
                status = "UnknownMessageId"
        else:
            status = "UnknownVenorId"

        #Send a conf
        conf_msg = [3, 
                    message[1],
                    "DataTransfer", 
                    {"status": status}]

        conf_send = json.dumps(conf_msg)
        print("Sending confirmation: " + conf_send)
        await self.my_websocket.send(conf_send)

    async def send_data_reserve(self):
        msg = ["chargerplus", "ReserveNow"]
        msg_send = json.dumps(msg)
        await self.my_websocket.send(msg_send)

    async def send_data_remote_start(self):
        msg = ["chargerplus", "RemoteStart"]
        msg_send = json.dumps(msg)
        await self.my_websocket.send(msg_send)

    async def send_data_remote_stop(self):
        msg = ["chargerplus", "RemoteStop"]
        msg_send = json.dumps(msg)
        await self.my_websocket.send(msg_send)

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
    qrCodeLayout =  [
                            [
                                sg.Image(data=displayStatus.qrCode(), key='QRCODE', size=(285,285)) 
                            ]
                        ]

    """ chargingPowerLayout =   [
                                [  
                                    sg.Text("0", font=('Lato', 20), key='TAMER', justification='center', text_color='white'),
                                    sg.Text("% kW", font=('Lato', 20), key='POWERKW', justification='center', text_color='white')
                                ]
                            ] """

    chargingTimeLayout =   [
                                [  
                                    sg.Text("0", font=('ITC Avant Garde Std Md', 160), key='PERCENT', text_color='Yellow')
                                ]
                            ]
    chargingPriceLayout =   [
                                [  
                                    sg.Text("", font=('Lato', 20), key='PRICE', justification='center', text_color='white'),
                                    sg.Text("SEK per KWH", font=('Lato', 20), key='PRICECURRENCY', justification='center', text_color='white')
                                ]
                            ]
    timeLayout =    [
                [
                   sg.Text("0", font=('ITC Avant Garde Std Md', 20), key='ID0', text_color='White'),
                   sg.Text("minutes", font=('ITC Avant Garde Std Md', 12), key='ID10', text_color='White'),
                   sg.Text("0", font=('ITC Avant Garde Std Md', 20), key='ID2', text_color='White'),
                   sg.Text("seconds until full", font=('ITC Avant Garde Std Md', 12), key='ID3', text_color='White')
                    
                ]
            ]
    lastPriceLayout =    [
                [
                   sg.Text("Total Price:", font=('Lato', 20), key='LASTPRICETEXT', justification='center', text_color='white'),
                   sg.Text("", font=('Lato', 20), key='LASTPRICE', justification='center', text_color='white'),
                   sg.Text("SEK", font=('Lato', 20), key='LASTPRICECURRENCY', justification='center', text_color='white')
                    
                ]
            ]

    usedKWHLayout =    [
            [
                sg.Text("100 kWh", font=('Lato', 20), key='KWH', justification='center', text_color='white')
                
            ]
        ]

    powerLayout =    [
            [
                sg.Text("", font=('Lato', 20), key='POWERTEST', justification='center', text_color='white'),
                sg.Text(" kWh", font=('Lato', 20), key='CHARGERPOWERKW', justification='center', text_color='white')
                
            ]
        ]

    Power_window = sg.Window(title="FlexiChargeChargingTimeWindow", layout=powerLayout, location=(162, 645), grab_anywhere=False, no_titlebar=True, background_color='black', margins=(0,0)).finalize()
    Power_window.TKroot["cursor"] = "none"
    Power_window.hide()

    UsedKWH_window = sg.Window(title="FlexiChargeChargingTimeWindow", layout=usedKWHLayout, location=(162, 645), grab_anywhere=False, no_titlebar=True, background_color='black', margins=(0,0)).finalize()
    UsedKWH_window.TKroot["cursor"] = "none"
    UsedKWH_window.hide()

    chargingLastPrice_window = sg.Window(title="FlexiChargeChargingTimeWindow", layout=lastPriceLayout, location=(125, 525), grab_anywhere=False, no_titlebar=True, background_color='black', margins=(0,0)).finalize()
    chargingLastPrice_window.TKroot["cursor"] = "none"
    chargingLastPrice_window.hide()
        
    time_window = sg.Window(title="FlexiChargeTopWindow", layout=timeLayout, location=(162, 685),keep_on_top=True, grab_anywhere=False, transparent_color=sg.theme_background_color(), no_titlebar=True).finalize()
    time_window.TKroot["cursor"] = "none"
    time_window.hide()

    background_Window = sg.Window(title="FlexiCharge", layout=startingUpLayout, no_titlebar=True, location=(0,0), size=(480, 800), keep_on_top=False).Finalize()
    background_Window.TKroot["cursor"] = "none"

    qrCode_window = sg.Window(title="FlexiChargeQrWindow", layout=qrCodeLayout, location=(95, 165), grab_anywhere=False, no_titlebar=True, size=(285,285), background_color='white', margins=(0,0)).finalize() #location=(95, 165) bildstorlek 285x285 från början
    qrCode_window.TKroot["cursor"] = "none"
    qrCode_window.hide()

    chargingPercent_window = sg.Window(title="FlexiChargeChargingPercentWindow", layout=chargingPercentLayout, location=(140, 245), grab_anywhere=False, no_titlebar=True, background_color='black', margins=(0,0)).finalize()
    chargingPercent_window.TKroot["cursor"] = "none"
    chargingPercent_window.hide()

    chargingPercentMark_window = sg.Window(title="FlexiChargeChargingPercentWindow", layout=chargingPercentMarkLayout, location=(276, 350), grab_anywhere=False, no_titlebar=True, background_color='black', margins=(0,0)).finalize()
    chargingPercentMark_window.TKroot["cursor"] = "none"
    chargingPercentMark_window.hide()

    """ chargingPower_window = sg.Window(title="FlexiChargeChargingPowerWindow", layout=chargingPowerLayout, location=(162, 645), grab_anywhere=False, no_titlebar=True, background_color='black', margins=(0,0)).finalize()
    chargingPower_window.TKroot["cursor"] = "none"
    chargingPower_window.hide()
 """
    chargingTime_window = sg.Window(title="FlexiChargeChargingTimeWindow", layout=chargingTimeLayout, location=(162, 694), grab_anywhere=False, no_titlebar=True, background_color='black', margins=(0,0)).finalize()
    chargingTime_window.TKroot["cursor"] = "none"
    chargingTime_window.hide()

    chargingPrice_window = sg.Window(title="FlexiChargeChargingTimeWindow", layout=chargingPriceLayout, location=(125, 525), grab_anywhere=False, no_titlebar=True, background_color='black', margins=(0,0)).finalize()
    chargingPrice_window.TKroot["cursor"] = "none"
    chargingPrice_window.hide()

    return background_Window, chargingPercent_window, chargingPercentMark_window, chargingTime_window, chargingPrice_window, qrCode_window, time_window, chargingLastPrice_window, UsedKWH_window, Power_window

window_back, window_chargingPercent, window_chargingPercentMark, window_chargingTime, window_chargingPrice, window_qrCode, window_time, window_chargingLastPrice, window_UsedKWH, window_power = GUI()

#update all the windows
def refreshWindows():
    global window_back, window_chargingTime, window_chargingPercent, window_chargingPrice, window_qrCode, window_time, window_chargingLastPrice, window_UsedKWH, window_power
    window_back.refresh()
    window_chargingTime.refresh()
    window_chargingPercent.refresh()
    window_chargingPercentMark.refresh()
    window_chargingPrice.refresh()
    window_qrCode.refresh()
    window_time.refresh()
    window_chargingLastPrice.refresh()
    window_UsedKWH.refresh()
    window_power.refresh()
            
async def statemachine(chargePoint : ChargePoint):

    global window_back, window_qrCode

    #instead of chargerID = 128321 you have to write the follwoing two rows(your ocpp code) to get 
    #the charge id from back-end and display it on screen

    #response = await ocpp_client.send_boot_notification()
    #chargerID = response.charger_id

    for i in range(20):
        await asyncio.gather(chargePoint.get_message())
        if chargePoint.charger_id != 000000:
            break
    
    if chargePoint.charger_id == 000000:
        state.set_state(States.S_NOTAVAILABLE)
        while True:
            state.set_state(States.S_NOTAVAILABLE)
            #Display QR code image
            window_back['IMAGE'].update(data=displayStatus.chargeNotAvailable())
            #update the window
            refreshWindows()

    chargerID = chargePoint.charger_id
    
    firstNumberOfChargerID = int(chargerID % 10) 
    secondNumberOfChargerID = int(chargerID/10) % 10 
    thirdNumberOfChargerID = int(chargerID/100) % 10  
    fouthNumberOfChargerID = int(chargerID/1000) % 10 
    fifthNumberOfChargerID = int(chargerID/10000) % 10 
    sixthNumberOfChargerID = int(chargerID/100000) % 10 
    
    chargerIdLayout =    [
                    [   
                        sg.Text(sixthNumberOfChargerID, font=('Tw Cen MT Condensed Extra Bold', 30), key='ID5', justification='center', pad=(25,0)),
                        sg.Text(fifthNumberOfChargerID, font=('Tw Cen MT Condensed Extra Bold', 30), key='ID4', justification='center', pad=(20,0)),
                        sg.Text(fouthNumberOfChargerID, font=('Tw Cen MT Condensed Extra Bold', 30), key='ID3', justification='center', pad=(25,0)),
                        sg.Text(thirdNumberOfChargerID, font=('Tw Cen MT Condensed Extra Bold', 30), key='ID2', justification='center', pad=(20,0)),
                        sg.Text(secondNumberOfChargerID, font=('Tw Cen MT Condensed Extra Bold', 30), key='ID1', justification='center', pad=(25,0)),
                        sg.Text(firstNumberOfChargerID, font=('Tw Cen MT Condensed Extra Bold', 30), key='ID0', justification='center', pad=(20,0))
                    ]
                ]

    chargerID_window = sg.Window(title="FlexiChargeTopWindow", layout=chargerIdLayout, location=(15,735),keep_on_top=True, grab_anywhere=False, transparent_color='white',background_color='white',size=(470,75), no_titlebar=True).finalize()
    chargerID_window.TKroot["cursor"] = "none"
    chargerID_window.hide()

    while True:
        await asyncio.gather(chargePoint.get_message())
        if state.get_state() == States.S_STARTUP:  
            continue

        elif state.get_state() == States.S_AVAILABLE:

            #Display QR code
            qr = qrcode.QRCode(
                version=8,
                error_correction=qrcode.constants.ERROR_CORRECT_L,
                box_size=5,
                border=4,
            )
            qr.add_data(chargerID)
            qr.make(fit=True)
            img_qrCodeGenerated = qr.make_image(fill_color="black", back_color="white")
            type(img_qrCodeGenerated)
            img_qrCodeGenerated.save("charger_images/qrCode.png")

            window_chargingPercent.hide()
            window_chargingPercentMark.hide()
            window_chargingTime.hide()
            window_power.hide()
            window_time.hide()
            window_chargingLastPrice.hide()
            window_UsedKWH.hide()

            #Display Charing id
            window_back['IMAGE'].update(data=displayStatus.chargingID())
            
            #Show QR code image on screen
            window_qrCode.UnHide()
            #Show Charger id on screen with QR code image
            chargerID_window.UnHide()
            #update the window
            refreshWindows() 

        elif state.get_state() == States.S_FLEXICHARGEAPP:
            window_back['IMAGE'].update(data=displayStatus.flexiChargeApp())
            #Hide the charge id on this state
            chargerID_window.Hide()
            window_qrCode.Hide()
            refreshWindows() 

        elif state.get_state() == States.S_PLUGINCABLE:

            window_qrCode.hide()
            window_back['IMAGE'].update(data=displayStatus.plugCable())
            window_chargingPrice.un_hide()
            #price = (ocpp)
            #window_chargingPrice['PRICE'].update(str(price))
            #Hide the charge id on this state
            chargerID_window.Hide()
            refreshWindows()  

        elif state.get_state() == States.S_CONNECTING:
            window_back['IMAGE'].update(data=displayStatus.connectingToCar())
            window_chargingPrice.hide()
            refreshWindows() 

        elif state.get_state() == States.S_CHARGING:
            num_of_secs = 100
            percent = 0

            window_back['IMAGE'].update(data=displayStatus.charging())

            #Display all the windows below during charging image shown on screen
            window_chargingPercent.un_hide()
            window_chargingPercentMark.un_hide()
            window_chargingTime.un_hide()
            #window_chargingPower.un_hide()
            window_time.un_hide()
            window_power.un_hide()
            
            timestamp_at_last_transfer = 0
            window_chargingPercent['PERCENT'].update(str(percent))
            window_chargingPercent.move(140, 245)
            while True:
                await asyncio.gather(chargePoint.get_message())

                if chargePoint.status != "Charging":
                    state.set_state(States.S_AVAILABLE)
                    break

                if (time.time() - timestamp_at_last_transfer) >= 1:
                    timestamp_at_last_transfer = time.time()
                    await asyncio.gather(chargePoint.send_data_transfer(1, percent))

                m, s = divmod(num_of_secs, 60)
            
                if percent >= 10:
                    #move charging percent on screen when percent >= 10
                    window_chargingPercent.move(60, 245)
                    #move the charging mark (%) on screen
                    window_chargingPercentMark.move(330, 350)                     
                if percent == 100:
                    await asyncio.gather(chargePoint.stop_transaction(False))
                    state.set_state(States.S_BATTERYFULL)
                    break

                refreshWindows()
                time.sleep(1)
                percent = percent + 1
                num_of_secs = num_of_secs - 1
                window_time['ID0'].update(str(m))
                window_time['ID2'].update(str(s))
                #update in precents how full the battery currently is 
                #window_chargingPower['TAMER'].update(str(power))
                window_chargingPercent['PERCENT'].update(str(percent))
                window_power['POWERTEST'].update(str(percent))
                
            

        elif state.get_state() == States.S_BATTERYFULL:

            #hide all the windows below during barttery full image shown on screen
            window_qrCode.hide()
            window_chargingPercent.hide()
            window_chargingPercentMark.hide()
            window_chargingTime.hide()
            window_power.hide()
            window_time.hide()
            window_chargingLastPrice.un_hide()
            window_UsedKWH.un_hide()
            lastPrice = 50
            window_chargingLastPrice['LASTPRICE'].update(str(lastPrice))
            window_back['IMAGE'].update(data=displayStatus.batteryFull())
            refreshWindows()
            await asyncio.sleep(5)
            state.set_state(States.S_AVAILABLE)

       

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

