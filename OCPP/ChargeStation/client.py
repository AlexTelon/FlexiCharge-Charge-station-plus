#Todo - Implement authorization cache (Not requirement)
#     - Implement authorization list (Might not be priority or required in this project)


import asyncio
from enum import Enum
from time import strptime
import websockets
from datetime import datetime
from dataclasses import dataclass

from ocpp.routing import on, after
from ocpp.v16 import ChargePoint as cp
from ocpp.v16.enums import Action, ChargePointErrorCode, RegistrationStatus, AuthorizationStatus, DataTransferStatus, ChargePointStatus, RemoteStartStopStatus, ReservationStatus
from ocpp.v16 import call_result, call
import json

class SampleValueContext(str, Enum):
    interruption_begin = "Interruption.Begin"
    interruption_end = "Interruption.End"
    sample_clock = "Sample.Clock"
    sample_periodic = "Sample.Periodic"
    transaction_begin = "Transaction.Begin"
    transaction_end = "Transaction.End"
    trigger = "Trigger"
    other = "Other"

class SampledValueFormat(str, Enum):
    raw = "Raw"
    signed_date = "SignedData"

class SampleValueMeasurand(str, Enum):
    energy_active_export_register = "Energy.Active.Export.Register"
    energy_active_import_register = "Energy.Active.Import.Register"
    energy_reactive_export_register = "Energy.Reactive.Export.Register"
    energy_reactive_import_register = "Energy.Reactive.Import.Register"
    energy_active_export_interval = "Energy.Active.Export.Interval"
    energy_active_import_interval = "Energy.Active.Import.Interval"
    energy_reactive_export_interval = "Energy.Reactive.Export.Interval"
    energy_reactive_import_interval = "Energy.Reactive.Import.Interval"
    power_active_export = "Power.Active.Export"
    power_active_import = "Power.Active.Import"
    power_offered = "Power.Offered"
    power_reactive_export = "Power.Reactive.Export"
    power_reactive_import = "Power.Reactive.Import"
    power_factor = "Power.Factor"
    current_import = "Current.Import"
    current_export = "Current.Export"
    current_offered = "Current.Offered"
    voltage = "Voltage"
    frequency = "Frequency"
    temperature = "Temperature"
    soc = "SoC"
    rpm = "RPM"

class SampleValuePhase(str, Enum):
    l1 = "L1"
    l2 = "L2"
    l3 = "L3"
    n = "N"
    l1_n = "L1-N"
    l2_n = "L2-N"
    l3_n = "L3-N"
    l1_l2 = "L1-L2"
    l2_l3 = "L2-L3"
    l3_l1 = "L3-L1"

class SampleValueLocation(str, Enum):
    cable = "Cable"
    ev = "EV"
    inlet = "Inlet"
    outlet = "Outlet"
    body = "Body"

class SampleValueUnit(str, Enum):
    wh = "Wh"
    kwh = "kWh"
    varh = "varh"
    kvarh = "kvarh"
    w = "W"
    kw = "kW"
    va = "VA"
    kva = "kVA"
    var = "var"
    kvar = "kvar"
    a = "A"
    v = "V"
    k = "K"
    celcius = "Celcius"
    celsius = "Celsius"
    fahrenheit = "Fahrenheit"
    percent = "Percent"
    hertz = "Hertz"

@dataclass
class SampledValue:
    value : str
    context : SampleValueContext
    format : SampledValueFormat
    measurand : SampleValueMeasurand
    phase : SampleValuePhase
    location : SampleValueLocation
    unit : SampleValueUnit

@dataclass
class MeterValues:
    timestamp : str
    sampled_value : SampledValue

class ChargePoint(cp):
    hardcoded_id_tag = "MyID"
    hardcoded_vendor_id = "vendorID"
    #A chargepoint could have more than one connector. Each connector should be numbered in order, starting with number one.
    #No number can be skipped. 0 is reserved for the entire chargepoint. In our chargeponit, we will simulate having 1 connector.
    hardcoded_connector_id = 1 #was 123 before
    hardcoded_meter_start = 10
    hardcoded_reservation_id = 1
    
    error_code = ChargePointErrorCode.no_error

    is_reserved = False

    my_websocket = None

    
    
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
        print(response.charger_id)
        print(response.current_time)

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

    @on(Action.ReserveNow)
    async def remote_reserve_now(self, connector_id:int, expiry_date:datetime, id_tag:str, reservation_id:int, parent_id_tag:str):
        print("Reserve now")
        if self.is_reserved == False:
            self.is_reserved = True
            response = call_result.ReserveNowPayload(
                status = ReservationStatus.accepted
            )
        else:
            response = call_result.ReserveNowPayload(
                status = ReservationStatus.occupied
            )
        return response

    async def send_data_transfer_req(self):
        msg = [1]
        msg_send = json.dumps(msg)
        await self.my_websocket.send(msg_send)

        #response = await self.my_websocket.recv()
        #print(json.loads(response))

        #await self._connection.send(msg_send)
            #print("Here")
            #res = self._connection.recv()
            #print(res)

        #print("Sending data transfer req")
        #request = call.DataTransferPayload(
            #vendor_id = "000001",
           # message_id = "166faaa2-8b5e-4d0a-a1bd-f7abaa3950dc",
            #data = "1"
        #)
        
        #response = await self.call(request)

        #if response.status == DataTransferStatus.accepted:
            #print("Data sent successfully")
        #elif response.status == DataTransferStatus.rejected:
            #Todo: Implement 
            #print("Data declined")





    #NOT FINISHED. ON HOLD.
    @on(Action.RemoteStartTransaction)
    async def remote_start_transaction(self, id_tag:str, connectorID:str="", chargingProfile:str=""):
        print("Remote start transaction called from central system")

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


    async def status_notification(self):
        current_time = datetime.now()
        timestamp = current_time.timestamp()
        formated_timestamp = current_time.strftime("%Y-%m-%dT%H:%M:%SZ") #Can be removed if back-end does not want the time-stamp formated
        
        request = call.StatusNotificationPayload(
            connector_id = self.hardcoded_connector_id,
            error_code = self.error_code.no_error,
            status = self.status,
            timestamp = str(timestamp), #Optional according to official OCPP-documentation
            info = None, #Optional according to official OCPP-documentation
            vendor_id = self.hardcoded_vendor_id, #Optional according to official OCPP-documentation
            vendor_error_code = None #Optional according to official OCPP-documentation
            )

        await self.call(request)
        print("Status notification sent!")
        
    #Known issue: Can't validate the payload. Probably because JSON expects array, and i don't know how to send an array to JSON? OCPP-library expect list?     
    async def send_meter_values(self, meter_values : MeterValues):
        sampled_value_JSON_array = {
            "value" : meter_values.sampled_value.value,
            "context" : meter_values.sampled_value.context,
            "format" : meter_values.sampled_value.format,
            "measurand" : meter_values.sampled_value.measurand,
            "phase" : meter_values.sampled_value.phase,
            "location" : meter_values.sampled_value.location,
            "unit" : meter_values.sampled_value.unit
        }

        meter_value_JSON_array = {
            "timestamp" : meter_values.timestamp,
            "sampledValue" : sampled_value_JSON_array
        }

        request = call.MeterValuesPayload(
            connector_id = self.hardcoded_connector_id,
            transaction_id = self.transaction_id,
            meter_value = meter_value_JSON_array
        )

        await self.call(request)

#This is a coroutine running in paralell with other coroutines
async def user_input_task(cp):
    #a = 0
    while 1:
        a = int(input(">> "))
        if a == 0:
            print("Testing " + str(a))
            await asyncio.gather(cp.send_boot_notification())
        elif a == 1:
            print("Testing " + str(a))
            await asyncio.gather(cp.send_authorization())
        elif a == 2:
            print("Testing " + str(a))
            await asyncio.gather(cp.on_heartbeat())
        elif a == 3:
            print("Testing " + str(a))
            await cp.send_data_transfer_req()
            await asyncio.sleep(1)  #Give program time to receive centralsystem initiated ReserveNow call
        elif a == 4:
            print("Testing " + str(a))
            #await asyncio.gather(cp.send_stop_transaction())
        elif a == 5:
            print("Testing " + str(a))
            await asyncio.gather(cp.send_start_transaction())
        elif a == 6:
            print("Testing " + str(a))
            await asyncio.gather(cp.status_notification())
        elif a == 7:
            print("Testing " + str(a))
            
            my_sampled_values = SampledValue
            my_sampled_values.value = "Test value"
            my_sampled_values.context = SampleValueContext.interruption_begin
            my_sampled_values.format = SampledValueFormat.raw
            my_sampled_values.measurand = SampleValueMeasurand.energy_active_export_interval
            my_sampled_values.phase = SampleValuePhase.l1
            my_sampled_values.location = SampleValueLocation.ev
            my_sampled_values.unit = SampleValueUnit.kwh

            my_meter_value = MeterValues
            my_meter_value.timestamp = datetime.now().timestamp()
            my_meter_value.sampled_value = my_sampled_values

            await asyncio.gather(cp.send_meter_values(my_meter_value))
        elif a == 9:
            #To pass on input. Needed when server is sending information
            await asyncio.sleep(2)
        #await asyncio.sleep(5)
        #a = (a + 1) % 5



async def main():
    async with websockets.connect(
        #'ws://localhost:9000/CP_1',
        'ws://54.220.194.65:1337/chargerplus',
         subprotocols=['ocpp1.6']
    ) as ws:
        cp = ChargePoint('chargerplus', ws)
        cp.my_websocket = ws
        #asyncio.gather(cp.generate_periodic_heartbeat(1))
        await asyncio.gather(cp.start(), user_input_task(cp))   #start() will keep program from continuing

if __name__ == '__main__':
    asyncio.run(main())