

class Reservation():
    def __init__(self):
        self._reserved_connector = None
        self._reserve_now_timer = 0
        self._is_reserved = False
        self._reservation_id_tag = None
        self._reservation_id = None

    # Get for reservation variables
    @property
    def is_reserved(self):
        return self._is_reserved

    @property
    def reservation_id_tag(self):
        return self._reservation_id_tag

    @property
    def reservation_id(self):
        return self._reservation_id

    @property
    def reserved_connector(self):
        return self._reserved_connector

    @property
    def reserve_now_timer(self):
        return self._reserve_now_timer

    # Setters
    @is_reserved.setter
    def is_reserved(self, boolean: bool):
        self._is_reserved = boolean

    @reservation_id_tag.setter
    def reservation_id_tag(self, reservation_id_tag):
        self._reservation_id_tag = reservation_id_tag

    @reservation_id.setter
    def reservation_id(self, reservation_id):
        self._reservation_id = reservation_id

    @reserved_connector.setter
    def reserved_connector(self, reserved_connector):
        self._reserved_connector = reserved_connector

    @reserve_now_timer.setter
    def reserve_now_timer(self, reserved_now_timer):
        self._reserve_now_timer = reserved_now_timer

    @reserve_now_timer.setter
    def decrement_reserve_now_timer_by(self, time: int):
        self._reserve_now_timer -= time
