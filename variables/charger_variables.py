
class Charger():
    def __init__(self):
        # Charger variables
        self._is_charging = False
        self._charging_id_tag = None
        self._charging_connector = None
        self._charger_id = 000000
        self._charging_Wh = 0  # I think this is how many Wh have been used to charge
        self._current_charging_percentage = 0
        self._meter_value_total = 0
    # Get for charging variables

    @property
    def charging_Wh(self):
        return self._charging_Wh

    @property
    def is_charging(self):
        return self._is_charging

    @property
    def charging_id_tag(self):
        return self._charging_id_tag

    @property
    def charging_connector(self):
        return self._charging_connector

    @property
    def current_charging_percentage(self):
        return self._current_charging_percentage

    @property
    def charger_id(self):
        return self._charger_id

     # Set for charging variables

    @charging_Wh.setter
    def charging_Wh(self, Wh: int):
        self._charging_Wh = Wh

    @is_charging.setter
    def is_charging(self, boolean: bool):
        self._is_charging = boolean

    @charger_id.setter
    def charger_id(self, id):
        self._charger_id = id

    @charging_id_tag.setter
    def charging_id_tag(self, charging_id_tag):
        self._charging_id_tag = charging_id_tag

    @charging_connector.setter
    def charging_connector(self, charging_connector):
        self._charging_connector = charging_connector

    @current_charging_percentage.setter
    def increment_current_charging_percentage_by(self, value: int):
        self._current_charging_percentage += value
        
    # Get for misc variables
    @property
    def meter_value_total(self):
        return self._meter_value_total

    # Set for misc variables
    @meter_value_total.setter
    def increment_meter_value_total_by(self, value: int):  # increment variable
        self._meter_value_total += value
