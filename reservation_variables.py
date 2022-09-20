

class Reservation():
    def __init__(self):
        self.reserved_connector = None
        self.reserve_now_timer = 0
        self.is_reserved = False
        self.reservation_id_tag = None
        self.reservation_id = None

    # Get for reservation variables
    @property
    def is_reserved(self):
        return self.is_reserved

    @property
    def reservation_id_tag(self):
        return self.reservation_id_tag

    @property
    def reservation_id(self):
        return self.reservation_id

    @property
    def reserved_connector(self):
        return self.reserved_connector

    @property
    def reserve_now_timer(self):
        return self.reserve_now_timer

    # Setters
    @is_reserved.setter
    def is_reserved(self, boolean: bool):
        self.is_reserved = boolean

    @reservation_id_tag.setter
    def reservation_id_tag(self, reservation_id_tag):
        self.reservation_id_tag = reservation_id_tag

    @reservation_id.setter
    def reservation_id(self, reservation_id):
        self.reservation_id = reservation_id

    @reserved_connector.setter
    def reserved_connector(self, reserved_connector):
        self.reserved_connector = reserved_connector

    @reserve_now_timer.setter
    def reserve_now_timer(self, reserved_now_timer):
        self.reserve_now_timer = reserved_now_timer

    @reserve_now_timer.setter
    def decrement_reserve_now_timer_by(self, time: int):
        self.reserve_now_timer -= time
