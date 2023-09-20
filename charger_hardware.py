import asyncio
from asyncio.events import get_event_loop
from asyncio.tasks import gather
import threading
from datetime import datetime
import time
from threading import Thread
from variables.charger_variables import Charger as ChargerVariables
from variables.reservation_variables import Reservation as ReservationVariables
from variables.misc_variables import Misc as MiscVariables
import platform
from ina219 import INA219
from ina219 import DeviceRangeError

if platform.system() == 'Linux':
    import RPi.GPIO as GPIO
    from mfrc522 import SimpleMFRC522
    import smbus


"""
Due to async funtions not being active in all cases.
Problems may occur in the future with certain functions due to lack of testing capabilities
Currently working as of 2022-09-14 - Kevin and Elin
"""


class Hardware():

    charger = ChargerVariables()
    misc = MiscVariables()
    reservation = ReservationVariables()
    hardcoded_rfid_token = 330174510923
    
    
    def meter_counter_charging(self):
        """
        If the car is charging, add 1 to the meter value and the current charging percentage, then send
        the data to the server, and start the function again.
        """

        #self.send_data_transfer is now in the web socket communication file. Should be removed from this file.

        if self.charger.is_charging == True:
            self.misc.increment_meter_value_total_by(1)
            self.charger.increment_current_charging_percentage_by(1)
            asyncio.run(self.send_data_transfer(
                1, self.charger.current_charging_percentage))
            threading.Timer(3, self.meter_counter_charging).start()
        else:
            print("{}{}".format("Total charge: ", self.misc.meter_value_total))

    def hard_reset_reservation(self):
        """
        It resets the reservation status of a parking spot
        """
        self.reservation.is_reserved = False
        self.reservation.reserve_now_timer = 0
        self.reservation.reservation_id_tag = None
        self.reservation.reservation_id = None
        print("Hard reset reservation")

    def hard_reset_charging(self):
        """
        It resets the charging status of the car
        """
        self.charger.is_charging = False
        self.charger.charging_id_tag = None
        self.charger.charging_connector = None
        print("Hard reset charging")

    def start_charging_from_reservation(self):
        """
        The function starts charging the EV, sets the charging_id_tag to the reservation_id_tag, and
        sets the charging_connector to the reserved_connector
        """
        self.charger.is_charging = True
        self.charger.charging_id_tag = self.reservation.reservation_id_tag
        self.charger.charging_connector = self.reservation.reserved_connector

    # Will count down every second
    def timer_countdown_reservation(self):
        """
        If the timer is 0, then the reservation is canceled, and the status is set to "Available"
        :return: The timer_countdown_reservation() function is being returned.
        """
        if self.reservation.reserve_now_timer <= 0:
            
         # self.send_status_notification and hard_reset_reservation is now in the web socket communication file. Should be removed from this file. 
         # The notification should probably be handeled in the state machine

            print("Reservation is canceled!")
            self.hard_reset_reservation()

            self.status = "Available"
            # Notify back-end that we are availiable again
            asyncio.run(self.send_status_notification(None))
            return

        self.reservation.decrement_reserve_now_timer_by(1)
        # Should only countdown if status us Reserved, otherwise won't be able to start charging
        if self.status == "Reserved":
            # Countdown every second
            threading.Timer(1, self.timer_countdown_reservation).start()

    def start_charging(self, connector_id, id_tag):
        """
        It starts a timer that calls the function meter_counter_charging every second
        :param connector_id: The connector ID of the connector that is being used for charging
        :param id_tag: The id_tag of the user who is charging
        """
        self.charger.is_charging = True
        self.charger.charging_id_tag = id_tag
        self.charger.charging_connector = connector_id
        threading.Timer(1, self.meter_counter_charging).start()

    def rfid_read(self):
        reader = SimpleMFRC522()
        try:
            print("Place tag")

            idToken, text = reader.read()
            print(idToken)
            print(text)

        finally:
            GPIO.cleanup()

        return idToken

    def rfid_write(self):
        reader = SimpleMFRC522()
        try:
            text = input("New Data: ")
            print("Place tag to write")
            reader.write(text)
            print("written")

        finally:
            GPIO.cleanup()

class INA219():
    SHUNT_OHMS = 0.1
    MAX_EXPECTED_AMPS = 3
    isConnected = False

    def __init__(self):
        self.init_INA219()

    def init_INA219(self):
        bus = smbus.SMBus(1)
        try:
            bus.write_quick(0x40)
            self.isConnected = True
            self.ina219 = INA219(self.SHUNT_OHMS, self.MAX_EXPECTED_AMPS)
            self.ina219.configure(self.ina219.RANGE_16V, bus_adc=self.ina219.ADC_128SAMP, shunt_adc=self.ina219.ADC_128SAMP)
        except Exception as e:
            self.isConnected = False
            print("Init Failed")

    def read_current_from_INA219(self):
        if(self.isConnected == True):
            try:
                print("Bus Current: %.3f mA" % self.ina219.current())
            except DeviceRangeError as e:
                print(e)
            return self.ina219.current
        else:
            print("INA219 is not connected")
            return -1
        
    def read_voltage_from_INA219(self):
        if(self.isConnected == True):
            print("Bus voltage: %.3f V" % self.ina219.voltage())
            return self.ina219.voltage
        else:
            print("INA219 is not connected")
            return -1