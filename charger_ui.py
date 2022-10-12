from sre_parse import State
from tkinter import Image
import PySimpleGUI as sg
from StateHandler import States
from images import Display
from charger_gui import GUI
import qrcode
from charger_window import Windows



class UI():
    WINDOW_GRAPHICS = Windows()
    current_state: State = None
    last_price = 50
    charger_id = 000000
    percent = 0
    power_charged = 0
    num_of_secs = 100
    #windowses = Windows()

    def __init__(self):
        self.WINDOW_GRAPHICS._background_window.finalize()

    def change_state(self, state: States):
        """
        It changes the state of the object to the state passed in as a parameter, and then runs the
        state
        :param state: States = States.START
        :type state: States
        """

        """"Kollar senaste window som den har gått ifrån"""
        if state != self.current_state:
            self.current_state = state
            self.run_state()

    def set_charger_id(self, id):
        """
        This function sets the charger_id attribute of the object to the value of the id parameter
        :param id: The ID of the charger
        """
        self.charger_id = id
        return self.charger_id

    def set_power_charged(self, power):
        self.power_charged = power

    def set_last_price(self, last_price):
        """
        It sets the last price of the charging
        :param last_price: The last price of the stock
        """
        self.last_price = last_price
        return self.last_price

    def set_charge_precentage(self, percentage: int):
        """
        It sets the charge percentage of the battery to the given percentage and then updates the
        charging status
        :param percentage: The percentage of the battery that is charged
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
        :param num_of_secs: The number of seconds the battery has been charging for
        """
        self.num_of_secs = num_of_secs_
        self.update_charging()


    def generate_qr_code(chargerID):
        """
        It takes a string and generates a QR code image from it.
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

        m, s = divmod(self.num_of_secs, 60)
        self.WINDOW_GRAPHICS._time_window['ID0'].update(str(m))
        self.WINDOW_GRAPHICS._time_window['ID2'].update(str(s))
        # update in precents how full the battery currently is
        # window_chargingPower['TAMER'].update(str(power))
        self.WINDOW_GRAPHICS._charging_percent_window['PERCENT'].update(str(self.percent))
        self.WINDOW_GRAPHICS._power_window['POWERTEST'].update(str(self.power_charged))
        
        if self.percent >= 10 and self.percent < 100:
            self.WINDOW_GRAPHICS._charging_percent_mark_window.move(330,350)
            self.WINDOW_GRAPHICS._charging_percent_window.move(100, 245)

        elif self.percent == 100:
            self.WINDOW_GRAPHICS._charging_percent_mark_window.move(370,350)
            self.WINDOW_GRAPHICS._charging_percent_window.move(20, 245)
        
        self.WINDOW_GRAPHICS._background_window.refresh()

    def run_state(self):
        """
        This function listens to which state the statemachine is currently in and
        Sets up the UI accordingly.
        It runs every time the change state is called and the state has changed from what it
        was before
        """
        
        #Loading window attributes from another class works.
        #TODO - A function must be created in the UI class that tracks the previous state it came from and close their window.

        if self.current_state == States.S_NOTAVAILABLE:
            #self.window_graphics._background_window.finalize()
            self.WINDOW_GRAPHICS._background_window['IMAGE'].update(data=Display.charge_not_available())
            self.WINDOW_GRAPHICS._background_window.refresh()

            
        elif self.current_state == States.S_STARTUP:
            #self.WINDOW_GRAPHICS._background_window.finalize()
            self.WINDOW_GRAPHICS._background_window['IMAGE'].update(data=Display.starting_up())
            self.WINDOW_GRAPHICS._background_window.refresh()

        elif self.current_state == States.S_AVAILABLE:
            #self.window_graphics._background_window.finalize()                 
            self.WINDOW_GRAPHICS._background_window['IMAGE'].update(data=Display.charging_id())
            self.WINDOW_GRAPHICS._qr_code_window.finalize()            
            self.WINDOW_GRAPHICS._charging_id_windows.finalize()
            self.WINDOW_GRAPHICS._background_window.refresh()

        
        elif self.current_state == States.S_AUTHORIZING:
            #self.window_graphics._background_window.finalize()   
            self.WINDOW_GRAPHICS._background_window.refresh()
            self.WINDOW_GRAPHICS._background_window['IMAGE'].update(data=Display.authorizing())
            self.WINDOW_GRAPHICS._background_window.refresh()


        elif self.current_state == States.S_FLEXICHARGEAPP:
            #self.window_graphics._background_window.finalize()
            self.WINDOW_GRAPHICS._background_window['IMAGE'].update(data=Display.flexi_charge_app())
            self.WINDOW_GRAPHICS._background_window.refresh()


        elif self.current_state == States.S_PLUGINCABLE:
            #self.window_graphics._background_window.finalize()
            self.WINDOW_GRAPHICS._background_window['IMAGE'].update(data=Display.plug_cable())
            self.WINDOW_GRAPHICS._charging_price_window.finalize()
            self.WINDOW_GRAPHICS._background_window.refresh()


        elif self.current_state == States.S_CONNECTING:
            #self.window_graphics._background_window.finalize()
            self.WINDOW_GRAPHICS._background_window['IMAGE'].update(data=Display.connecting_to_car())
            self.WINDOW_GRAPHICS._background_window.refresh()


        elif self.current_state == States.S_CHARGING:
            #self.window_graphics._background_window.finalize()
            self.WINDOW_GRAPHICS._background_window['IMAGE'].update(data=Display.charging())
            self.WINDOW_GRAPHICS._charging_percent_window.finalize()
            self.WINDOW_GRAPHICS._charging_percent_mark_window.finalize()
            self.WINDOW_GRAPHICS._time_window.finalize()
            self.WINDOW_GRAPHICS._power_window.finalize()
            self.WINDOW_GRAPHICS._charging_percent_window['PERCENT'].update(str(self.percent))
            self.WINDOW_GRAPHICS._power_window['POWERTEST'].update(str(self.power_charged))

            if self.percent == 100:
                self.WINDOW_GRAPHICS._charging_percent_mark_window.move(370,350)
                self.WINDOW_GRAPHICS._charging_percent_window.move(20, 245)
            
            elif self.percent >= 10:
                self.WINDOW_GRAPHICS._charging_percent_mark_window.move(330, 350)
                self.WINDOW_GRAPHICS._charging_percent_window.move(100, 245)

            else:
                self.WINDOW_GRAPHICS._charging_percent_mark_window.move(250, 350)
                self.WINDOW_GRAPHICS._charging_percent_window.move(140, 245)

            self.WINDOW_GRAPHICS._background_window.refresh()


             
             
        elif self.current_state == States.S_DISCONNECT:
            #self.window_graphics._background_window.finalize()
            self.WINDOW_GRAPHICS._background_window['IMAGE'].update(data=Display.disconnecting_from_car())
            self.WINDOW_GRAPHICS._background_window.refresh()

        elif self.current_state == States.S_BATTERYFULL:
            # hide all the windows below during barttery full image shown on screen
            self.WINDOW_GRAPHICS._charging_last_price_window['LASTPRICE'].update(
                str(self.last_price))
            self.WINDOW_GRAPHICS._background_window['IMAGE'].update(data=Display.battery_full())
            self.WINDOW_GRAPHICS._background_window.refresh()
