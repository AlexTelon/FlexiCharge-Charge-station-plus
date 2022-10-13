import PySimpleGUI as sg
from charger_gui import GUI
from images import Display

class Windows(): 

    sg.theme('black')
    FLEXI_GUI = GUI()

    def __init__(self):
        # Creating a window with the title "FlexiCharge" and the layout of the start_layout.
        self._background_window = sg.Window(title="FlexiCharge", 
        layout=self.FLEXI_GUI.start_layout, 
        no_titlebar=True, 
        location=(0, 0), 
        size=(480, 800), 
        keep_on_top=False)

        # Creating a window with the title "FlexiChargeChargingTimeWindow" and the layout of the power_layout.
        self._power_window = sg.Window(title="FlexiChargeChargingTimeWindow",
        layout=self.FLEXI_GUI.power_layout, 
        location=(162, 645), 
        grab_anywhere=False, 
        no_titlebar=True, 
        background_color='black', 
        margins=(0, 0))

        # Creating a window with the title "FlexiChargeChargingTimeWindow" and the layout of the used_kwd.
        self._usedkwh_window = sg.Window(title="FlexiChargeChargingTimeWindow", 
        layout=self.FLEXI_GUI.used_kwd, location=(162, 645), 
        grab_anywhere=False, 
        no_titlebar=True, 
        background_color='black', 
        margins=(0, 0))


        # Creating a window with the title "FlexiChargeChargingTimeWindow" and the layout of the
        # last_price.
        self._charging_last_price_window = sg.Window(title="FlexiChargeChargingTimeWindow", 
        layout=self.FLEXI_GUI.last_price, 
        location=(125, 525), 
        grab_anywhere=False, 
        no_titlebar=True, 
        background_color='black', 
        margins=(0, 0))

        # Creating a window with the title "FlexiChargeTopWindow" and the layout of the time_layout.
        self._time_window = sg.Window(title="FlexiChargeTopWindow", 
        layout=self.FLEXI_GUI.time_layout, 
        location=(162, 685), 
        keep_on_top=True, 
        grab_anywhere=False, 
        transparent_color=sg.theme_background_color(),
        no_titlebar=True)


        # Creating a window with the title "FlexiChargeQrWindow" and the layout of the qr_code_layout.
        self._qr_code_window = sg.Window(title="FlexiChargeQrWindow", 
        layout=self.FLEXI_GUI.qr_code_layout, 
        location=(95, 165),
        grab_anywhere=False, 
        no_titlebar=True, 
        size=(285, 285), 
        background_color='white',
        margins=(0, 0))
        

        # Creating a window with the title "FlexiChargeChargingPercentWindow" and the layout of the
        # charging_percent.
        self._charging_percent_window = sg.Window(title="FlexiChargeChargingPercentWindow", 
        layout=self.FLEXI_GUI.charging_percent,
        location=(140, 245), 
        grab_anywhere=False, 
        no_titlebar=True,
        background_color='black', 
        margins=(0, 0))

        # Creating a window with the title "FlexiChargeChargingPercentWindow" and the layout of the
        # charging_percent_mark.
        self._charging_percent_mark_window = sg.Window(title="FlexiChargeChargingPercentWindow",
        layout=self.FLEXI_GUI.charging_percent_mark, 
        location=(276, 350), 
        grab_anywhere=False, 
        no_titlebar=True, 
        transparent_color='black', 
        margins=(0, 0))


        # Creating a window with the title "FlexiChargeChargingTimeWindow" and the layout of the
        # charging_price_layout.
        self._charging_price_window = sg.Window(title="FlexiChargeChargingTimeWindow", 
        layout=self.FLEXI_GUI.charging_price_layout, 
        location=(125, 525), 
        grab_anywhere=False, 
        no_titlebar=True, 
        background_color='black', 
        margins=(0, 0))
