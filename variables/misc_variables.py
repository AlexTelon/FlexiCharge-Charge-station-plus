
class Misc():
    def __init__(self):
        self._meter_value_total = 0
        self._status = "Available"

    # Get for misc variables
    @property
    def meter_value_total(self):
        return self._meter_value_total

    @property
    def status(self):
        return self._status

    # Set for misc variables
    @meter_value_total.setter
    def increment_meter_value_total_by(self, value: int):  # increment variable
        self._meter_value_total += value

    @status.setter
    def status(self, status):
        self._status = status



