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


if platform.system() == 'Linux':
    import RPi.GPIO as GPIO
    from mfrc522 import SimpleMFRC522
    import smbus2
    import serial
    from ina219 import INA219
    from ina219 import DeviceRangeError





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
    __SHUNT_OHMS = 0.1
    __MAX_EXPECTED_AMPS = 3
    __ina219_is_Connected = False
    __ser = None
    __start_time = 0
    __timeout = 0

    def __init__(self):
        if platform.system() == 'Linux':
            self.init_INA219()
            self.init_UART()
        else:
            pass

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

    def calc_power_hour(self, W: float, T: float ):
        self.charger.charging_Wh = self.charger.charging_Wh + (W * (T/3600))               
            
    def calc_power(self, V: float, A: float ):
        self.charger.charging_W = V * A  
        return self.charger.charging_W

    def init_UART(self):
        """
        This method initializes a UART communication port.
        - It specifies the serial port ('/dev/ttyS0') and baud rate (115200) for the UART connection.
        - The 'timeout' parameter is set to 1 second, which means that read operations will wait for up to 1 second for data to arrive.
        - Finally, it flushes the input and output buffers of the UART.
        """
        serial_port = '/dev/ttyS0'
        baud_rate = 115200
        self.__ser = serial.Serial(serial_port, baud_rate, timeout=1)
        self.__ser.flush()

    def read_via_UART(self):
        """
        This method reads data from a UART and 
        processes incoming commands and append charger variables

        If there is incoming data, it is read and processed based on the following commands:

        - "connect": Marks the charger as connected, then sends "ok" to BMS.
        - "end": Marks the charger as disconnected and stops charging, then sends "ok" to BMS.
        - "begin" (only if the charger is already connected): Initiates charging and records the start time, then sends "ok" to BMS.
        - "beep": Heart beat from BMS. Updates the start time.
        - If none of the above commands and the charger is connected, it parses commands in the format "key:value" and updates charger parameters accordingly.

        If no "beep" command is received within 0.6 second after the last action, the charger is marked as disconnected and charging is stopped.
        """
        if self.__ser.in_waiting > 0:
            try: #incomming data need to be a string or cstring otherwise the code will crash
                line = self.__ser.readline().decode('utf-8').rstrip()
                #print(line)
                if line == "connect" and self.charger.is_connected == False and self.charger.is_charging == False:
                    self.charger.is_connected = True
                    self.update_timeout()
                    self.__ser.write(b"ok\n")
                    self.__ser.flushInput()

                elif line == "end":
                    self.charger.is_connected = False
                    self.charger.is_charging = False
                    self.charger.requsted_voltage = ""
                    self.__ser.write(b"ok\n")
                    self.__ser.flushInput()

                elif line == "begin" and self.charger.is_connected == True and self.charger.is_charging == False and self.charger.requsted_voltage != "":
                    self.charger.is_charging = True
                    self.__start_time = time.time()
                    self.__ser.write(b"ok\n")
                    self.__ser.flushInput()

                elif line == "beep":
                    self.__start_time = time.time()
                    self.__ser.flushInput()

                elif self.charger.is_connected == True:
                    try:
                        parts = line.split(":")
                        key = parts[0]
                        value = parts[1]
                        if key == "voltage":
                            self.charger.requsted_voltage = value
                            self.__start_time = time.time()
                            self.__ser.write(b"ok\n")
                        elif key == "charge":
                            self.charger.current_charging_percentage = int(value)
                            self.__start_time = time.time()
                        elif key == "temp":
                            self.charger.battrey_temp = int(value)
                            self.__start_time = time.time()
                        self.__ser.flushInput()
                    except:
                        pass
            except serial.SerialException as e:
                print(e)

        if time.time() - self.__start_time >= 0.6 and self.charger.is_connected and self.charger.is_charging and self.charger.requsted_voltage != "": # Check if 0.6 seconds passed and got no beep, cut power
            self.charger.is_connected = False
            self.charger.is_charging = False
            self.charger.requsted_voltage = ""
            self.__ser.flushInput()



    def init_INA219(self):
        """
        This method initializes the INA219 current/voltage sensor and checks for its connection.

        - It first attempts to establish communication with the INA219 sensor at address 0x40.
        - If successful, it marks the INA219 as connected.
        - It then creates an instance of the INA219 class with predefined shunt resistance and expected current values.
        - The sensor is configured to operate with a voltage range of 16V and high-resolution ADC settings.
        """
        bus = smbus2.SMBus(1)
        try:
            bus.write_quick(0x40)
            self.__ina219_is_Connected = True
            self.ina219 = INA219(self.__SHUNT_OHMS, self.__MAX_EXPECTED_AMPS)
            self.ina219.configure(self.ina219.RANGE_16V, bus_adc=self.ina219.ADC_128SAMP, shunt_adc=self.ina219.ADC_128SAMP)
        except Exception as e:
            self.__ina219_is_Connected = False
            print("Init Failed")

    def read_current_from_INA219(self):
        """
        This method reads the current value from the INA219 current/voltage sensor if it is connected.
        - If the INA219 is connected, it attempts to read the current value from the sensor.
        Returns:
            - If the INA219 is connected and the reading is successful, it returns the current value in mA.
            - If the INA219 is not connected, it returns -1.
        """
        if(self.__ina219_is_Connected == True):
            #try:
            #    print("Bus Current: %.3f mA" % self.ina219.current())
            #except DeviceRangeError as e:
            #    print(e)
            return self.ina219.current()
        else:
            #print("INA219 is not connected")
            return -1
        
    def read_voltage_from_INA219(self):
        """
        This method reads the voltage value from the INA219 current/voltage sensor if it is connected.
        - If the reading is successful, it returns the voltage value in volts (V).
        Returns:
            - If the INA219 is connected and the reading is successful, it returns the voltage value in V.
            - If the INA219 is not connected, it returns -1.
        """
        if(self.__ina219_is_Connected == True):
            #print("Bus voltage: %.3f V" % self.ina219.voltage())
            return self.ina219.voltage()
        else:
            #print("INA219 is not connected")
            return -1
            
    def controll_output_voltage(self, voltage):
        """
        Control the output voltage by toggling GPIO pins for relays.

        :param voltage: The desired voltage level ("off", "3.3v", "4.2v", "7.4v", "9v", "5v", "6v", "10v", "11.5v").
        :return: -1 if an invalid voltage is provided.
        """
        GPIO.setmode(GPIO.BCM)

        relay_pins = [21, 20, 16, 12, 26, 19, 13, 6] 
        
        GPIO.setup(relay_pins, GPIO.OUT)
        GPIO.output(relay_pins, GPIO.HIGH)

        if voltage == "off":
            pass
        elif voltage == "3.3":
            GPIO.output(21, GPIO.LOW)
        elif voltage == "4.2":
            GPIO.output(20, GPIO.LOW)
        elif voltage == "7.4":
            GPIO.output(16, GPIO.LOW)
        elif voltage == "9":
            GPIO.output(12, GPIO.LOW)
        elif voltage == "5":
            GPIO.output(6, GPIO.LOW)
        elif voltage == "6":
            GPIO.output(13, GPIO.LOW)
        elif voltage == "10":
            GPIO.output(19, GPIO.LOW)
        elif voltage == "11.5":
            GPIO.output(26, GPIO.LOW)
        else:
            print("Invalid voltage")
            return -1
        return 0   


    def get_charger_variables(self):    
        """
        Get the current charger variables.
        :return: The current charger variables.
        """
        return self.charger
    
    def set_charger_variables(self, new_variables):
        """
        Set the charger variables to a new set of variables.
        """
        self.charger = new_variables
    
    def is_connected(self):
        """
        This function checks if the charger is connected to a vehicle.
        :return: True if connected and charging, False otherwise.
        """
        if self.charger.is_charging == False or self.charger.is_connected == False:
            return False
        else:   
            return True
        
    def timeout_passed_and_not_connected(self):
        """
        This function checks if the timeout(15sec) has passed and the charger is not connected to a vehicle or not charging.
        :return: True if the timeout has passed, False otherwise.
        """
        if time.time() - self.__timeout >= 15 and (self.charger.is_charging == False or self.charger.is_connected == False or self.charger.requsted_voltage == ""):
            return True
        else:
            return False
        
    def update_timeout(self):
        """
        Update the timeout value to the current time.
        """
        self.__timeout = time.time()

