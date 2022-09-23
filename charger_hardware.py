import asyncio
from asyncio.events import get_event_loop
from asyncio.tasks import gather
import threading
from datetime import datetime
import time
import asyncio
from threading import Thread
from variables.charger_variables import Charger
from variables.reservation_variables import Reservation
from variables.misc_variables import Misc
"""
Due to async funtions not being active in all cases.
Problems may occur in the future with certain functions due to lack of testing capabilities
Currently working as of 2022-09-14 - Kevin and Elin
"""


class Hardware():

    charger = Charger()
    misc = Misc()
    reservation = Reservation()

    def meter_counter_charging(self):
        """
        If the car is charging, add 1 to the meter value and the current charging percentage, then send
        the data to the server, and start the function again.
        """

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
        # threading.Timer(1, self.meter_counter_charging).start()
        # threading.Timer(2, self.send_periodic_meter_values).start()

    # Will count down every second
    def timer_countdown_reservation(self):
        """
        If the timer is 0, then the reservation is canceled, and the status is set to "Available"
        :return: The timer_countdown_reservation() function is being returned.
        """
        if self.reservation.reserve_now_timer <= 0:
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
