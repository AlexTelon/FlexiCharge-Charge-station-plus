
class Misc():
    def __init__(self):
        self.meter_value_total = 0

    # Get for misc variables
    @property
    def meter_value_total(self):
        return self.meter_value_total

    # Set for misc variables
    @meter_value_total.setter
    def increment_meter_value_total_by(self, value: int):  # increment variable
        self.meter_value_total += value
