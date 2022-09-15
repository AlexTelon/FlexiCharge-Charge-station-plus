import asyncio
from asyncio.events import get_event_loop
from asyncio.tasks import gather
import threading
from datetime import datetime
import time
import asyncio
from threading import Thread

"""
Due to async funtions not being active in all cases. 
Problems may occur in the future with certain functions due to lack of testing capabilities
Currently working as of 2022-09-14 - Kevin and Elin
"""


class Hardware():
    """ 
    # Reservation related variables

    ReserveConnectorZeroSupported = True
    """

    reserved_connector = None
    reserve_now_timer = 0
    is_reserved = False
    reservation_id_tag = None
    reservation_id = None

    meter_value_total = 0
    current_charging_percentage = 0

    # Transaction related variables
    is_charging = False
    charging_id_tag = None
    charging_connector = None
    charging_Wh = 0  # I think this is how many Wh have been used to charge

    # Getter and Setter for charging
    def get_charging_Wh(self):
        return self.charging_Wh

    def set_charging_Wh(self, Wh: int):
        self.charging_Wh = Wh

    def get_is_charging(self):
        return self.is_charging

    def set_is_charging(self, boolean: bool):
        self.is_charging = boolean

    def get_charging_id_tag(self):
        return self.charging_id_tag

    def set_charging_id_tag(self, charging_id_tag):
        self.charging_id_tag = charging_id_tag

    def get_charging_connector(self):
        return self.charging_connector

    def set_charging_connector(self, charging_connector):
        self.charging_connector = charging_connector

    def get_current_charging_percentage(self):
        return self.current_charging_percentage

    # Getter and Setter for reservation

    def get_is_reserved(self):
        return self.is_reserved

    def set_is_reserved(self, boolean: bool):
        self.is_reserved = boolean

    def get_reservation_id_tag(self):
        return self.reservation_id_tag

    def set_reservation_id_tag(self, reservation_id_tag):
        self.reservation_id_tag = reservation_id_tag

    def get_reservation_id(self):
        return self.reservation_id

    def set_reservation_id(self, reservation_id):
        self.reservation_id = reservation_id

    def get_reserved_connector(self):
        return self.reserved_connector

    def set_reserved_connector(self, reserved_connector):
        self.reserved_connector = reserved_connector

    def get_reserve_now_timer(self):
        return self.reserve_now_timer

    def set_reserve_now_timer(self, time: int):
        self.reserve_now_timer = time

    # Getter and Setter for misc

    def get_meter_value_total(self):
        return self.meter_value_total

    def meter_counter_charging(self):
        """
        If the car is charging, add 1 to the meter value and the current charging percentage, then send
        the data to the server, and start the function again.
        """
        if self.is_charging == True:
            self.meter_value_total = self.meter_value_total + 1
            self.current_charging_percentage = self.current_charging_percentage + 1
            asyncio.run(self.send_data_transfer(
                1, self.current_charging_percentage))
            threading.Timer(3, self.meter_counter_charging).start()
        else:
            print("{}{}".format("Total charge: ", self.meter_value_total))

    def hard_reset_reservation(self):
        """
        It resets the reservation status of a parking spot
        """
        self.set_is_reserved = False
        self.reserve_now_timer = 0
        self.set_reservation_id_tag = None
        self.set_reservation_id = None
        print("Hard reset reservation")

    def hard_reset_charging(self):
        """
        It resets the charging status of the car
        """
        self.set_is_charging = False
        self.charging_id_tag = None
        self.charging_connector = None
        print("Hard reset charging")

    def start_charging_from_reservation(self):
        """
        The function starts charging the EV, sets the charging_id_tag to the reservation_id_tag, and
        sets the charging_connector to the reserved_connector
        """
        self.set_is_charging = True
        self.charging_id_tag = self.reservation_id_tag
        self.charging_connector = self.reserved_connector
        #threading.Timer(1, self.meter_counter_charging).start()
        #threading.Timer(2, self.send_periodic_meter_values).start()

    # Will count down every second
    def timer_countdown_reservation(self):
        """
        If the timer is 0, then the reservation is canceled, and the status is set to "Available"
        :return: The timer_countdown_reservation() function is being returned.
        """
        if self.reserve_now_timer <= 0:
            print("Reservation is canceled!")
            self.hw.hard_reset_reservation()
            self.status = "Available"
            # Notify back-end that we are availiable again
            asyncio.run(self.send_status_notification(None))
            return
        self.reserve_now_timer = self.reserve_now_timer - 1
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
        self.set_is_charging = True
        self.charging_id_tag = id_tag
        self.charging_connector = connector_id
        threading.Timer(1, self.meter_counter_charging).start()