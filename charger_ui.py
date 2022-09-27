from sre_parse import State
import PySimpleGUI as sg
from StateHandler import States
from images import Display
import qrcode


class UI():
    current_state: State = None
    last_price = 50
    charger_id = 000000
    percent = 0
    num_of_secs = 100

    def __init__(self, state: State,):
        self.current_state = state

    def change_state(self, state: States):
        """
        It changes the state of the object to the state passed in as a parameter, and then runs the
        state

        :param state: States = States.START
        :type state: States
        """
        if state != self.current_state:
            self.current_state = state
            self.run_state()

    def set_charger_id(self, id):
        """
        This function sets the charger_id attribute of the object to the value of the id parameter

        :param id: The ID of the charger
        """
        self.charger_id = id

    def set_last_price(self, last_price):
        """
        It sets the last price of the charging

        :param last_price: The last price of the stock
        """
        self.last_price = last_price

    def set_charge_precentage(self, percentage):
        """
        It sets the charge percentage of the battery to the given percentage and then updates the
        charging status

        :param percentage: The percentage of the battery that is charged
        """
        self.percent = percentage
        self.update_charging()

    def set_num_of_secs(self, num_of_secs):
        """
        It sets the number of seconds to charge the battery.

        :param num_of_secs: The number of seconds the battery has been charging for
        """
        self.num_of_secs = num_of_secs
        self.update_charging()

    def GUI():
        """
        It creates a bunch of windows and returns them.
        :return: the windows that are created in the function.
        """
        sg.theme('black')

        starting_up_layout = [
            [
                sg.Image(data=Display.starting_up(), key='IMAGE',
                         pad=((0, 0), (0, 0)), size=(480, 800))
            ]
        ]

        charging_percent_layout = [
            [
                sg.Text("0", font=('ITC Avant Garde Std Md', 160),
                        key='PERCENT', text_color='Yellow')
            ]
        ]

        charging_percent_mark_layout = [
            [
                sg.Text("%", font=('ITC Avant Garde Std Md', 55),
                        key='PERCENTMARK', text_color='Yellow')
            ]
        ]
        qr_code_layout = [
            [
                sg.Image(data=Display.qr_code(),
                         key='QRCODE', size=(285, 285))
            ]
        ]

        """ chargingPowerLayout =   [
                                    [  
                                        sg.Text("0", font=('Lato', 20), key='TAMER', justification='center', text_color='white'),
                                        sg.Text("% kW", font=('Lato', 20), key='POWERKW', justification='center', text_color='white')
                                    ]
                                ] """

        """ charging_time_layout = [
            [
                sg.Text("0", font=(
                    'ITC Avant Garde Std Md', 160), key='PERCENT', text_color='Blue')
            ]
        ] """
        charging_price_layout = [
            [
                sg.Text("", font=('Lato', 20), key='PRICE',
                        justification='center', text_color='white'),
                sg.Text("SEK per KWH", font=(
                    'Lato', 20), key='PRICECURRENCY', justification='center', text_color='white')
            ]
        ]
        time_layout = [
            [
                sg.Text("0", font=('ITC Avant Garde Std Md', 20),
                        key='ID0', text_color='White'),
                sg.Text("minutes", font=('ITC Avant Garde Std Md', 12),
                        key='ID10', text_color='White'),
                sg.Text("0", font=('ITC Avant Garde Std Md', 20),
                        key='ID2', text_color='White'),
                sg.Text("seconds until full", font=(
                    'ITC Avant Garde Std Md', 12), key='ID3', text_color='White')

            ]
        ]
        last_price_layout = [
            [
                sg.Text("Total Price:", font=('Lato', 20), key='LASTPRICETEXT',
                        justification='center', text_color='white'),
                sg.Text("", font=('Lato', 20), key='LASTPRICE',
                        justification='center', text_color='white'),
                sg.Text("SEK", font=('Lato', 20), key='LASTPRICECURRENCY',
                        justification='center', text_color='white')

            ]
        ]

        used_kwh_layout = [
            [
                sg.Text("100 kWh", font=('Lato', 20), key='KWH',
                        justification='center', text_color='white')

            ]
        ]

        power_layout = [
            [
                sg.Text("", font=('Lato', 20), key='POWERTEST',
                        justification='center', text_color='white'),
                sg.Text(" kWh", font=('Lato', 20), key='CHARGERPOWERKW',
                        justification='center', text_color='white')

            ]
        ]
        power_window = sg.Window(title="FlexiChargeChargingTimeWindow", layout=power_layout, location=(
            162, 645), grab_anywhere=False, no_titlebar=True, background_color='black', margins=(0, 0)).finalize()
        power_window.TKroot["cursor"] = "none"
        power_window.hide()

        usedkwh_window = sg.Window(title="FlexiChargeChargingTimeWindow", layout=used_kwh_layout, location=(
            162, 645), grab_anywhere=False, no_titlebar=True, background_color='black', margins=(0, 0)).finalize()
        usedkwh_window.TKroot["cursor"] = "none"
        usedkwh_window.hide()

        charging_last_price_window = sg.Window(title="FlexiChargeChargingTimeWindow", layout=last_price_layout, location=(
            125, 525), grab_anywhere=False, no_titlebar=True, background_color='black', margins=(0, 0)).finalize()
        charging_last_price_window.TKroot["cursor"] = "none"
        charging_last_price_window.hide()

        time_window = sg.Window(title="FlexiChargeTopWindow", layout=time_layout, location=(
            162, 685), keep_on_top=True, grab_anywhere=False, transparent_color=sg.theme_background_color(),
            no_titlebar=True).finalize()
        time_window.TKroot["cursor"] = "none"
        time_window.hide()

        background_window = sg.Window(title="FlexiCharge", layout=starting_up_layout, no_titlebar=True, location=(
            0, 0), size=(480, 800), keep_on_top=False).Finalize()
        background_window.TKroot["cursor"] = "none"

        qr_code_window = sg.Window(title="FlexiChargeQrWindow", layout=qr_code_layout, location=(95, 165),
                                   grab_anywhere=False, no_titlebar=True, size=(

            285, 285), background_color='white',
            margins=(0, 0)).finalize()  # location=(95, 165) bildstorlek 285x285 från början
        qr_code_window.TKroot["cursor"] = "none"
        qr_code_window.hide()

        charging_percent_window = sg.Window(title="FlexiChargeChargingPercentWindow", layout=charging_percent_layout,
                                            location=(
                                                140, 245), grab_anywhere=False, no_titlebar=True,
                                            background_color='black', margins=(0, 0)).finalize()
        charging_percent_window.TKroot["cursor"] = "none"
        charging_percent_window.hide()

        charging_percent_mark_window = sg.Window(title="FlexiChargeChargingPercentWindow",
                                               layout=charging_percent_mark_layout, location=(
                                                   276, 350), grab_anywhere=False, no_titlebar=True, transparent_color='black', margins=(0, 0)).finalize()
        charging_percent_mark_window.TKroot["cursor"] = "none"
        charging_percent_mark_window.hide()

        """ chargingPower_window = sg.Window(title="FlexiChargeChargingPowerWindow", layout=chargingPowerLayout, location=(162, 645), grab_anywhere=False, no_titlebar=True, background_color='black', margins=(0,0)).finalize()
        chargingPower_window.TKroot["cursor"] = "none"
        chargingPower_window.hide()
     """
        """ charging_time_window = sg.Window(title="FlexiChargeChargingTimeWindow", layout=charging_time_layout, location=(
            162, 694), grab_anywhere=False, no_titlebar=True, background_color='black', margins=(0, 0)).finalize()
        charging_time_window.TKroot["cursor"] = "none"
        charging_time_window.hide() """

        charging_price_window = sg.Window(title="FlexiChargeChargingTimeWindow", layout=charging_price_layout, location=(
            125, 525), grab_anywhere=False, no_titlebar=True, background_color='black', margins=(0, 0)).finalize()
        charging_price_window.TKroot["cursor"] = "none"
        charging_price_window.hide()

        return background_window, charging_percent_window, charging_percent_mark_window,  charging_price_window, qr_code_window, time_window, charging_last_price_window, usedkwh_window, power_window

    window_back, window_charging_percent, window_charging_percent_mark,  window_charging_price, window_qr_code, window_time, window_charging_last_price, window_used_kwh, window_power = GUI()

    # update all the windows

    def refresh_windows(self):
        """
        It refreshes all the windows
        """
        self.window_charging_percent.refresh()
        self.window_charging_percent.refresh()
        self.window_charging_price.refresh()
        self.window_qr_code.refresh()
        self.window_time.refresh()
        self.window_charging_last_price.refresh()
        self.window_used_kwh.refresh()
        self.window_power.refresh()

    def hide_all_windows(self):
        """
        Hide_all_windows() hides all the windows in the program
        """
        self.window_qr_code.hide()
        self.window_charging_percent.hide()
        self.window_charging_percent_mark.hide()
        self.window_power.hide()
        self.window_time.hide()
        self.window_charging_last_price.un_hide()
        self.window_used_kwh.un_hide()

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

    """
    This function updates the charging screen to match the current charged precent and time
    left.
    """

    def update_charging(self):
        m, s = divmod(self.num_of_secs, 60)
        self.window_time['ID0'].update(str(m))
        self.window_time['ID2'].update(str(s))
        # update in precents how full the battery currently is
        # window_chargingPower['TAMER'].update(str(power))
        self.window_charging_percent['PERCENT'].update(str(self.percent))
        self.window_power['POWERTEST'].update(str(self.percent))
        self.refresh_windows()

    def run_state(self):
        """
        This function listens to which state the statemachine is currently in and
        Sets up the UI accordingly.
        It runs every time the change state is called and the state has changed from what it
        was before
        """

        if self.current_state == States.S_NOTAVAILABLE:
            self.window_back['IMAGE'].update(
                data=Display.charge_not_available())
            # update the window
            self.refresh_windows()
        elif self.current_state == States.S_STARTUP:
            # It should probably do something here later but i need to find out what
            do_something = None

        elif self.current_state == States.S_AVAILABLE:

            # Starts by generating a new qr code depending on the charger ID

            # TODO
            # Prompts bugg because of name convention
            # self.generate_qr_code(self.charger_id)
            self.window_charging_percent.hide()
            self.window_charging_percent_mark.hide()
            self.window_power.hide()
            self.window_time.hide()
            self.window_charging_last_price.hide()
            self.window_used_kwh.hide()

            # Display Charing id
            self.window_back['IMAGE'].update(data=Display.charging_id())

            # Show QR code image on screen
            self.window_qr_code.UnHide()
            # Show Charger id on screen with QR code image
            #self.chargerID_window.UnHide()#
            # update the window
            self.refresh_windows()

        elif self.current_state == States.S_FLEXICHARGEAPP:
            self.window_back['IMAGE'].update(data=Display.flexi_charge_app())
            # Hide the charge id on this state
            # self.chargerID_window.Hide()
            self.window_qr_code.Hide()
            self.refresh_windows()

        elif self.current_state == States.S_PLUGINCABLE:
            self.window_qr_code.hide()
            self.window_back['IMAGE'].update(data=Display.plug_cable())
            self.window_charging_price.un_hide()
            # Hide the charge id on this state
            # self.chargerID_window.Hide()
            self.refresh_windows()

        elif self.current_state == States.S_CONNECTING:
            self.window_back['IMAGE'].update(data=Display.connecting_to_car())
            self.window_charging_price.hide()
            self.refresh_windows()

        elif self.current_state == States.S_CHARGING:
            if self.percent >= 100:
                  self.change_state(States.S_BATTERYFULL)
                
            
            else: 
                self.window_back['IMAGE'].update(data=Display.charging())
                # Display all the windows below during charging image shown on screen
                self.window_charging_percent.un_hide()
                self.window_charging_percent_mark.un_hide()
                self.window_time.un_hide()
                self.window_power.un_hide()
                self.window_charging_percent['PERCENT'].update(str(self.percent))
                if self.percent >= 10:
                    self.window_charging_percent_mark.move(330, 350)
                    self.window_charging_percent.move(100, 245)
                else:
                    self.window_charging_percent.move(140, 245)
                    self.window_charging_percent_mark.move(250, 350)               
                self.update_charging()

        elif self.current_state == States.S_BATTERYFULL:
            # hide all the windows below during barttery full image shown on screen
            self.hide_all_windows()
            self.window_charging_last_price['LASTPRICE'].update(
                str(self.last_price))
            self.window_back['IMAGE'].update(data=Display.battery_full())
            self.refresh_windows()
