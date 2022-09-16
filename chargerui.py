from sre_parse import State
import PySimpleGUI as sg
from StateHandler import States
from images import DisplayStatus
import qrcode


class ChargerGUI():
    current_state : State = None
    last_price = 50
    charger_id = 000000
    percent = 0
    num_of_secs = 100
    
    def __init__(self, state: State,):
        self.current_state = state

    def change_state(self,state: States):
        if state != self.current_state:
            self.current_state = state
            self.run_state()
    def set_charger_id(self,id):
        self.charger_id = id
    def set_last_price(self, last_price):
        self.last_price = last_price
    def set_charge_precentage(self,percentage):
        self.percent = percentage
        self.update_charging()
    def set_num_of_secs(self,num_of_secs):
        self.num_of_secs = num_of_secs
        self.update_charging()
    
    def GUI():
        """
        It creates a bunch of windows and returns them.
        :return: the windows that are created in the function.
        """
        sg.theme('black')

        startingUpLayout = [
            [
                sg.Image(data=DisplayStatus.starting_up(), key='IMAGE',
                         pad=((0, 0), (0, 0)), size=(480, 800))
            ]
        ]

        chargingPercentLayout = [
            [
                sg.Text("0", font=('ITC Avant Garde Std Md', 160),
                        key='PERCENT', text_color='Yellow')
            ]
        ]

        chargingPercentMarkLayout = [
            [
                sg.Text("%", font=('ITC Avant Garde Std Md', 55),
                        key='PERCENTMARK', text_color='Yellow')
            ]
        ]
        qrCodeLayout = [
            [
                sg.Image(data=DisplayStatus.qr_code(),
                         key='QRCODE', size=(285, 285))
            ]
        ]

        """ chargingPowerLayout =   [
                                    [  
                                        sg.Text("0", font=('Lato', 20), key='TAMER', justification='center', text_color='white'),
                                        sg.Text("% kW", font=('Lato', 20), key='POWERKW', justification='center', text_color='white')
                                    ]
                                ] """

        chargingTimeLayout = [
            [
                sg.Text("0", font=(
                    'ITC Avant Garde Std Md', 160), key='PERCENT', text_color='Yellow')
            ]
        ]
        chargingPriceLayout = [
            [
                sg.Text("", font=('Lato', 20), key='PRICE',
                        justification='center', text_color='white'),
                sg.Text("SEK per KWH", font=(
                    'Lato', 20), key='PRICECURRENCY', justification='center', text_color='white')
            ]
        ]
        timeLayout = [
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
        lastPriceLayout = [
            [
                sg.Text("Total Price:", font=('Lato', 20), key='LASTPRICETEXT',
                        justification='center', text_color='white'),
                sg.Text("", font=('Lato', 20), key='LASTPRICE',
                        justification='center', text_color='white'),
                sg.Text("SEK", font=('Lato', 20), key='LASTPRICECURRENCY',
                        justification='center', text_color='white')

            ]
        ]

        usedKWHLayout = [
            [
                sg.Text("100 kWh", font=('Lato', 20), key='KWH',
                        justification='center', text_color='white')

            ]
        ]

        powerLayout = [
            [
                sg.Text("", font=('Lato', 20), key='POWERTEST',
                        justification='center', text_color='white'),
                sg.Text(" kWh", font=('Lato', 20), key='CHARGERPOWERKW',
                        justification='center', text_color='white')

            ]
        ]
        Power_window = sg.Window(title="FlexiChargeChargingTimeWindow", layout=powerLayout, location=(
            162, 645), grab_anywhere=False, no_titlebar=True, background_color='black', margins=(0, 0)).finalize()
        Power_window.TKroot["cursor"] = "none"
        Power_window.hide()

        UsedKWH_window = sg.Window(title="FlexiChargeChargingTimeWindow", layout=usedKWHLayout, location=(
            162, 645), grab_anywhere=False, no_titlebar=True, background_color='black', margins=(0, 0)).finalize()
        UsedKWH_window.TKroot["cursor"] = "none"
        UsedKWH_window.hide()

        chargingLastPrice_window = sg.Window(title="FlexiChargeChargingTimeWindow", layout=lastPriceLayout, location=(
            125, 525), grab_anywhere=False, no_titlebar=True, background_color='black', margins=(0, 0)).finalize()
        chargingLastPrice_window.TKroot["cursor"] = "none"
        chargingLastPrice_window.hide()

        time_window = sg.Window(title="FlexiChargeTopWindow", layout=timeLayout, location=(
            162, 685), keep_on_top=True, grab_anywhere=False, transparent_color=sg.theme_background_color(),
                                no_titlebar=True).finalize()
        time_window.TKroot["cursor"] = "none"
        time_window.hide()

        background_Window = sg.Window(title="FlexiCharge", layout=startingUpLayout, no_titlebar=True, location=(
            0, 0), size=(480, 800), keep_on_top=False).Finalize()
        background_Window.TKroot["cursor"] = "none"

        qrCode_window = sg.Window(title="FlexiChargeQrWindow", layout=qrCodeLayout, location=(95, 165),
                                  grab_anywhere=False, no_titlebar=True, size=(
                285, 285), background_color='white',
                                  margins=(0, 0)).finalize()  # location=(95, 165) bildstorlek 285x285 från början
        qrCode_window.TKroot["cursor"] = "none"
        qrCode_window.hide()

        chargingPercent_window = sg.Window(title="FlexiChargeChargingPercentWindow", layout=chargingPercentLayout,
                                           location=(
                                               140, 245), grab_anywhere=False, no_titlebar=True,
                                           background_color='black', margins=(0, 0)).finalize()
        chargingPercent_window.TKroot["cursor"] = "none"
        chargingPercent_window.hide()

        chargingPercentMark_window = sg.Window(title="FlexiChargeChargingPercentWindow",
                                               layout=chargingPercentMarkLayout, location=(
                276, 350), grab_anywhere=False, no_titlebar=True, background_color='black', margins=(0, 0)).finalize()
        chargingPercentMark_window.TKroot["cursor"] = "none"
        chargingPercentMark_window.hide()

        """ chargingPower_window = sg.Window(title="FlexiChargeChargingPowerWindow", layout=chargingPowerLayout, location=(162, 645), grab_anywhere=False, no_titlebar=True, background_color='black', margins=(0,0)).finalize()
        chargingPower_window.TKroot["cursor"] = "none"
        chargingPower_window.hide()
     """
        chargingTime_window = sg.Window(title="FlexiChargeChargingTimeWindow", layout=chargingTimeLayout, location=(
            162, 694), grab_anywhere=False, no_titlebar=True, background_color='black', margins=(0, 0)).finalize()
        chargingTime_window.TKroot["cursor"] = "none"
        chargingTime_window.hide()

        chargingPrice_window = sg.Window(title="FlexiChargeChargingTimeWindow", layout=chargingPriceLayout, location=(
            125, 525), grab_anywhere=False, no_titlebar=True, background_color='black', margins=(0, 0)).finalize()
        chargingPrice_window.TKroot["cursor"] = "none"
        chargingPrice_window.hide()

        return background_Window, chargingPercent_window, chargingPercentMark_window, chargingTime_window, chargingPrice_window, qrCode_window, time_window, chargingLastPrice_window, UsedKWH_window, Power_window

    window_back, window_chargingPercent, window_chargingPercentMark, window_chargingTime, window_chargingPrice, window_qrCode, window_time, window_chargingLastPrice, window_UsedKWH, window_power = GUI()

    # update all the windows

    def refresh_windows(self):
        """
        It refreshes all the windows
        """
        self.window_chargingTime.refresh()
        self.window_chargingPercent.refresh()
        self.window_chargingPercent.refresh()
        self.window_chargingPrice.refresh()
        self.window_qrCode.refresh()
        self.window_time.refresh()
        self.window_chargingLastPrice.refresh()
        self.window_UsedKWH.refresh()
        self.window_power.refresh()


    def hide_all_windows(self):
        self.window_qrCode.hide()
        self.window_chargingPercent.hide()
        self.window_chargingPercentMark.hide()
        self.window_chargingTime.hide()
        self.window_power.hide()
        self.window_time.hide()
        self.window_chargingLastPrice.un_hide()
        self.window_UsedKWH.un_hide()

        
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
        img_qrCodeGenerated = qr.make_image(
            fill_color="black", back_color="white")
        type(img_qrCodeGenerated)
        img_qrCodeGenerated.save("charger_images/qrCode.png")

    def update_charging(self):
        m, s = divmod(self.num_of_secs, 60)
        self.window_time['ID0'].update(str(m))
        self.window_time['ID2'].update(str(s))
         # update in precents how full the battery currently is
         # window_chargingPower['TAMER'].update(str(power))
        self.window_chargingPercent['PERCENT'].update(str(self.percent))
        self.window_power['POWERTEST'].update(str(self.percent))

    def run_state(self):
        if self.current_state == States.S_NOTAVAILABLE:
            self.window_back['IMAGE'].update(
                data=DisplayStatus.charge_not_available())
            # update the window
            self.refresh_windows()
        elif self.current_state == States.S_STARTUP:
            #It should probably do something here later but i need to find out what
            do_something = None
            
        elif self.current_state == States.S_AVAILABLE:
            #Starts by generating a new qr code depending on the charger ID
            
            self.generate_qr_code(self.chargerID)

            self.window_chargingPercent.hide()
            self.window_chargingPercentMark.hide()
            self.window_chargingTime.hide()
            self.window_power.hide()
            self.window_time.hide()
            self.window_chargingLastPrice.hide()
            self.window_UsedKWH.hide()

            # Display Charing id
            self.window_back['IMAGE'].update(data=DisplayStatus.charging_id())

            # Show QR code image on screen
            self.window_qrCode.UnHide()
            # Show Charger id on screen with QR code image
            self.chargerID_window.UnHide()
            # update the window
            self.refresh_windows()
        
        elif self.current_state == States.S_FLEXICHARGEAPP:
            self.window_back['IMAGE'].update(data=DisplayStatus.flexi_charge_app())
            # Hide the charge id on this state
            self.chargerID_window.Hide()
            self.window_qrCode.Hide()
            self.refresh_windows()

        elif self.current_state == States.S_PLUGINCABLE:
            self.window_qrCode.hide()
            self.window_back['IMAGE'].update(data=DisplayStatus.plug_cable())
            self.window_chargingPrice.un_hide()
            # Hide the charge id on this state
            self.chargerID_window.Hide()
            self.refresh_windows()

        elif self.current_state == States.S_CONNECTING:
            self.window_back['IMAGE'].update(data=DisplayStatus.connecting_to_car())
            self.window_chargingPrice.hide()
            self.refresh_windows()
        
        elif self.change_state == States.S_CHARGING:
            self.window_back['IMAGE'].update(data=DisplayStatus.charging())
            # Display all the windows below during charging image shown on screen
            self.window_chargingPercent.un_hide()
            self.window_chargingPercentMark.un_hide()
            self.window_chargingTime.un_hide()
            self.window_time.un_hide()
            self.window_power.un_hide()
            self.window_chargingPercent['PERCENT'].update(str(self.percent))
            self.window_chargingPercent.move(140, 245)

            if self.percent >= 10:
                # move charging percent on screen when percent >= 10
                self.window_chargingPercent.move(60, 245)
                # move the charging mark (%) on screen
                self.window_chargingPercentMark.move(330, 350)
            self.refresh_windows()
            self.update_charging()

        elif self.current_state == States.S_BATTERYFULL:
            # hide all the windows below during barttery full image shown on screen
            self.hide_all_windows()
            self.window_chargingLastPrice['LASTPRICE'].update(str(self.last_price))
            self.window_back['IMAGE'].update(data=DisplayStatus.battery_full())
            self.refresh_windows()

            



