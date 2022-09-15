from platform import machine
import PySimpleGUI as sg
import asyncio
import time

from StateHandler import States
from StateHandler import StateHandler
from images import displayStatus

import qrcode
import asyncio
from asyncio.events import get_event_loop
from asyncio.tasks import gather
import threading
import websockets
from datetime import datetime
import time
import json
import asyncio
from threading import Thread

class chargerGUI():
    def GUI(state: States):
        """
        It creates a bunch of windows and returns them.
        :return: the windows that are created in the function.
        """
        sg.theme('black')

        startingUpLayout = [
            [
                sg.Image(data=displayStatus.startingUp(), key='IMAGE',
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
                sg.Image(data=displayStatus.qrCode(),
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

    def refreshWindows():
        """
        It refreshes all the windows
        """
        global window_back, window_chargingTime, window_chargingPercent, window_chargingPrecentMark, window_chargingPrice, window_qrCode, window_time, window_chargingLastPrice, window_UsedKWH, window_power
        window_back.refresh()
        window_chargingTime.refresh()
        window_chargingPercent.refresh()
        window_chargingPercentMark.refresh()
        window_chargingPrice.refresh()
        window_qrCode.refresh()
        window_time.refresh()
        window_chargingLastPrice.refresh()
        window_UsedKWH.refresh()
        window_power.refresh()

    



