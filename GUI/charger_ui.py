from sre_parse import State
from tkinter import Image
import PySimpleGUI as sg
from numpy import char
from StateHandler import States
from images import Display
from GUI.charger_gui import GUI
import qrcode
from GUI.charger_window import Windows
from websocket_communication import CHARGER_VARIABLES



class UI():
    WINDOW_GRAPHICS = Windows()
    current_state: State = None
    last_price = 50
    charging_price = 0
    charger_id = 000000
    percent = 0
    power_charged = 0
    num_of_secs = 100
    charging_is_done = False
    charger_id_displayed = False

    def __init__(self):
        """
        It initialize and builds the window when you run the code.
        """
        self.WINDOW_GRAPHICS._background_window.finalize()

    #TODO - A function should be created which keeps track of which window was previously open and unhide its attribute if necessary.

    def change_state(self, state: States):
        """
        If the state is not the same as the current state, then set the current state to the new state and
        run the state
        
        :param state: The state to change to
        :type state: States
        """
        if state != self.current_state:
            self.current_state = state
            self.run_state()
    
    def set_charging_price(self, newPrice):
        self.charging_price = newPrice
        

    #TODO - Needs to be troubleshooted of how to display the charger_id in the most efficient way
    def set_charger_id(self, id):
        """
        It sets the charger id
        
        :param id: The ID of the charger
        :return: The charger ID
        """

        self.charger_id = id
        return self.charger_id
 
    def set_power_charged(self, power):
        """
        The function takes in a parameter called power, and sets the power_charged attribute to the
        value of the power parameter
        
        :param power: The power of the charging
        :return: The power_charged attribute is being returned.
        """
        self.power_charged = power
        return self.power_charged

    def set_last_price(self, last_price):
        """
        It sets the last price of the stock.
        
        :param last_price: The last price of the last charging occurence.
        :return: The price of the last charging occurence.
        """   
        self.last_price = last_price
        return self.last_price

    def set_charge_precentage(self, percentage: int):
        """
        It takes an integer as an argument and returns the same integer if it's less than 100, otherwise it
        returns 100
        
        :param percentage: The percentage of the battery that is charged
        :type percentage: int
        :return: The percentage of the battery charge.
        """
        self.percent = percentage

        if self.percent >= 100:
            self.percent = 100
            return self.percent
        else:
            self.percent = percentage
            return self.percent


    def set_num_of_secs(self, num_of_secs_):
        """
        It sets the number of seconds to charge the battery.
        
        :param num_of_secs_: The number of seconds the battery has been charging for
        """

        self.num_of_secs = num_of_secs_
        self.update_charging()


    def generate_qr_code(self,chargerID):
        """
        It takes a string and generates a QR code image from it
        
        :param chargerID: The ID of the charger
        """

        qr = qrcode.QRCode(
            version=8,
            error_correction=qrcode.constants.ERROR_CORRECT_L,
            box_size=5,
            border=4,
        )
        qr.add_data(chargerID)
        qr.make(fit=True)
        img_qr_codegenerated = qr.make_image(
            fill_color="black", back_color="white")
        type(img_qr_codegenerated)
        img_qr_codegenerated.save("charger_images/qrCode.png")
                
    def update_charging(self):
        """
        It updates the charging window with the time, percent, and power charged.
        """
        m, s = divmod(self.num_of_secs, 60)
        self.WINDOW_GRAPHICS._time_window['ID0'].update(str(m))
        self.WINDOW_GRAPHICS._time_window['ID2'].update(str(s))
        self.WINDOW_GRAPHICS._charging_percent_window['PERCENT'].update(str(self.percent))
        self.WINDOW_GRAPHICS._power_window['POWERTEST'].update(str(self.power_charged))
        self.WINDOW_GRAPHICS._charging_price_window['PRICE'].update(str(self.charging_price))
        
        if self.percent >= 10 and self.percent < 100:
            self.WINDOW_GRAPHICS._charging_percent_mark_window.move(350,350)
            self.WINDOW_GRAPHICS._charging_percent_window.move(80, 245)

        elif self.percent == 100:
            self.WINDOW_GRAPHICS._charging_percent_mark_window.move(400,350)
            self.WINDOW_GRAPHICS._charging_percent_window.move(0, 245)
        
        self.WINDOW_GRAPHICS._background_window.refresh()


    def run_state(self):
        """
        It's a function that updates the GUI based on the current state of the program
        """

        if self.current_state == States.S_NOTAVAILABLE:
            self.WINDOW_GRAPHICS._background_window['IMAGE'].update(data=Display.charge_not_available())
            self.WINDOW_GRAPHICS._background_window.refresh()

            
        elif self.current_state == States.S_STARTUP:
            self.WINDOW_GRAPHICS._background_window['IMAGE'].update(data=Display.starting_up())
            self.WINDOW_GRAPHICS._background_window.refresh()

        #TODO - Attribute to display charger id needs to be implemented.
        elif self.current_state == States.S_AVAILABLE:
            if self.charging_is_done:
                self.WINDOW_GRAPHICS._charging_last_price_window.hide()
                self.WINDOW_GRAPHICS._qr_code_window.un_hide()            
            self.WINDOW_GRAPHICS._background_window['IMAGE'].update(data=Display.charging_id())
            self.WINDOW_GRAPHICS._qr_code_window.finalize()            
            self.WINDOW_GRAPHICS._background_window.refresh()

        elif self.current_state == States.S_AUTHORIZING:
            self.WINDOW_GRAPHICS._qr_code_window.hide()
            self.WINDOW_GRAPHICS._background_window['IMAGE'].update(data=Display.authorizing())
            self.WINDOW_GRAPHICS._background_window.refresh()


        elif self.current_state == States.S_FLEXICHARGEAPP:
            self.WINDOW_GRAPHICS._qr_code_window.hide()
            self.WINDOW_GRAPHICS._background_window['IMAGE'].update(data=Display.flexi_charge_app())
            self.WINDOW_GRAPHICS._background_window.refresh()


        elif self.current_state == States.S_PLUGINCABLE:
            self.WINDOW_GRAPHICS._qr_code_window.hide()
            self.WINDOW_GRAPHICS._background_window['IMAGE'].update(data=Display.plug_cable())
            self.WINDOW_GRAPHICS._background_window.refresh()


        elif self.current_state == States.S_CONNECTING:
            self.WINDOW_GRAPHICS._background_window['IMAGE'].update(data=Display.connecting_to_car())
            self.WINDOW_GRAPHICS._background_window.refresh()


        elif self.current_state == States.S_CHARGING:
            self.charging_is_done = False
            #self.WINDOW_GRAPHICS._qr_code_window.hide()
            self.WINDOW_GRAPHICS._background_window['IMAGE'].update(data=Display.charging())
            self.WINDOW_GRAPHICS._charging_percent_window.finalize()
            self.WINDOW_GRAPHICS._charging_percent_mark_window.finalize()
            self.WINDOW_GRAPHICS._time_window.finalize()
            self.WINDOW_GRAPHICS._power_window.finalize()
            self.WINDOW_GRAPHICS._charging_price_window.finalize()
            self.WINDOW_GRAPHICS._charging_price_window['PRICE'].update(str(CHARGER_VARIABLES.charging_price))
            self.WINDOW_GRAPHICS._charging_percent_window['PERCENT'].update(str(self.percent))
            self.WINDOW_GRAPHICS._power_window['POWERTEST'].update(str(self.power_charged))

            if self.percent == 100:
                self.WINDOW_GRAPHICS._charging_percent_mark_window.move(400,350)
                self.WINDOW_GRAPHICS._charging_percent_window.move(0, 245)
            
            elif self.percent >= 10:
                self.WINDOW_GRAPHICS._charging_percent_mark_window.move(350, 350)
                self.WINDOW_GRAPHICS._charging_percent_window.move(80, 245)

            else:
                self.WINDOW_GRAPHICS._charging_percent_mark_window.move(270, 350)
                self.WINDOW_GRAPHICS._charging_percent_window.move(120, 245)

            self.WINDOW_GRAPHICS._background_window.refresh()
             
             
        elif self.current_state == States.S_DISCONNECT:
            self.WINDOW_GRAPHICS._background_window['IMAGE'].update(data=Display.disconnecting_from_car())
            self.WINDOW_GRAPHICS._background_window.refresh()

        elif self.current_state == States.S_BATTERYFULL:
            self.WINDOW_GRAPHICS._charging_percent_window.hide()
            self.WINDOW_GRAPHICS._charging_percent_mark_window.hide()
            self.WINDOW_GRAPHICS._time_window.hide()
            self.WINDOW_GRAPHICS._power_window.hide()
            self.WINDOW_GRAPHICS._charging_last_price_window.finalize()
            self.charging_is_done = True
            self.WINDOW_GRAPHICS._charging_last_price_window['LASTPRICE'].update(
                str(self.last_price))
            self.WINDOW_GRAPHICS._background_window['IMAGE'].update(data=Display.battery_full())
            self.WINDOW_GRAPHICS._background_window.refresh()
