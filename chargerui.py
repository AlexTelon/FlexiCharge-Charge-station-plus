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
    def GUI():
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
        global window_back, window_chargingTime, window_chargingPercent, window_chargingPrice, window_qrCode, window_time, window_chargingLastPrice, window_UsedKWH, window_power
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

    async def statemachine(chargePoint: ChargePoint):
        """
        The function is a state machine that changes the state of the charge point and displays the relevant
        image on the screen

        :param chargePoint: The ChargePoint object that is used to communicate with the OCPP server
        :type chargePoint: ChargePoint
        """

        global window_back, window_qrCode

        # instead of chargerID = 128321 you have to write the follwoing two rows(your ocpp code) to get
        # the charge id from back-end and display it on screen

        # response = await ocpp_client.send_boot_notification()
        # chargerID = response.charger_id

        for i in range(20):
            await asyncio.gather(chargePoint.get_message())
            if chargePoint.charger_id != 000000:
                break

        if chargePoint.charger_id == 000000:
            state.set_state(States.S_NOTAVAILABLE)
            while True:
                state.set_state(States.S_NOTAVAILABLE)
                # Display QR code image
                window_back['IMAGE'].update(
                    data=displayStatus.chargeNotAvailable())
                # update the window
                refreshWindows()

        chargerID = chargePoint.charger_id

        firstNumberOfChargerID = int(chargerID % 10)
        secondNumberOfChargerID = int(chargerID / 10) % 10
        thirdNumberOfChargerID = int(chargerID / 100) % 10
        fouthNumberOfChargerID = int(chargerID / 1000) % 10
        fifthNumberOfChargerID = int(chargerID / 10000) % 10
        sixthNumberOfChargerID = int(chargerID / 100000) % 10

        chargerIdLayout = [
            [
                sg.Text(sixthNumberOfChargerID, font=(
                    'Tw Cen MT Condensed Extra Bold', 30), key='ID5', justification='center', pad=(25, 0)),
                sg.Text(fifthNumberOfChargerID, font=(
                    'Tw Cen MT Condensed Extra Bold', 30), key='ID4', justification='center', pad=(20, 0)),
                sg.Text(fouthNumberOfChargerID, font=(
                    'Tw Cen MT Condensed Extra Bold', 30), key='ID3', justification='center', pad=(25, 0)),
                sg.Text(thirdNumberOfChargerID, font=(
                    'Tw Cen MT Condensed Extra Bold', 30), key='ID2', justification='center', pad=(20, 0)),
                sg.Text(secondNumberOfChargerID, font=(
                    'Tw Cen MT Condensed Extra Bold', 30), key='ID1', justification='center', pad=(25, 0)),
                sg.Text(firstNumberOfChargerID, font=(
                    'Tw Cen MT Condensed Extra Bold', 30), key='ID0', justification='center', pad=(20, 0))
            ]
        ]

        chargerID_window = sg.Window(title="FlexiChargeTopWindow", layout=chargerIdLayout, location=(15, 735),
                                     keep_on_top=True,
                                     grab_anywhere=False, transparent_color='white', background_color='white',
                                     size=(470, 75), no_titlebar=True).finalize()
        chargerID_window.TKroot["cursor"] = "none"
        chargerID_window.hide()

        while True:
            await asyncio.gather(chargePoint.get_message())
            if state.get_state() == States.S_STARTUP:
                continue

            elif state.get_state() == States.S_AVAILABLE:

                # Display QR code
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

                window_chargingPercent.hide()
                window_chargingPercentMark.hide()
                window_chargingTime.hide()
                window_power.hide()
                window_time.hide()
                window_chargingLastPrice.hide()
                window_UsedKWH.hide()

                # Display Charing id
                window_back['IMAGE'].update(data=displayStatus.chargingID())

                # Show QR code image on screen
                window_qrCode.UnHide()
                # Show Charger id on screen with QR code image
                chargerID_window.UnHide()
                # update the window
                refreshWindows()

            elif state.get_state() == States.S_FLEXICHARGEAPP:
                window_back['IMAGE'].update(data=displayStatus.flexiChargeApp())
                # Hide the charge id on this state
                chargerID_window.Hide()
                window_qrCode.Hide()
                refreshWindows()

            elif state.get_state() == States.S_PLUGINCABLE:

                window_qrCode.hide()
                window_back['IMAGE'].update(data=displayStatus.plugCable())
                window_chargingPrice.un_hide()
                # price = (ocpp)
                # window_chargingPrice['PRICE'].update(str(price))
                # Hide the charge id on this state
                chargerID_window.Hide()
                refreshWindows()

            elif state.get_state() == States.S_CONNECTING:
                window_back['IMAGE'].update(data=displayStatus.connectingToCar())
                window_chargingPrice.hide()
                refreshWindows()

            elif state.get_state() == States.S_CHARGING:
                num_of_secs = 100
                percent = 0

                window_back['IMAGE'].update(data=displayStatus.charging())

                # Display all the windows below during charging image shown on screen
                window_chargingPercent.un_hide()
                window_chargingPercentMark.un_hide()
                window_chargingTime.un_hide()
                # window_chargingPower.un_hide()
                window_time.un_hide()
                window_power.un_hide()

                timestamp_at_last_transfer = 0
                window_chargingPercent['PERCENT'].update(str(percent))
                window_chargingPercent.move(140, 245)
                while True:
                    await asyncio.gather(chargePoint.get_message())

                    if chargePoint.status != "Charging":
                        state.set_state(States.S_AVAILABLE)
                        break

                    if (time.time() - timestamp_at_last_transfer) >= 1:
                        timestamp_at_last_transfer = time.time()
                        await asyncio.gather(chargePoint.send_data_transfer(1, percent))

                    m, s = divmod(num_of_secs, 60)

                    if percent >= 10:
                        # move charging percent on screen when percent >= 10
                        window_chargingPercent.move(60, 245)
                        # move the charging mark (%) on screen
                        window_chargingPercentMark.move(330, 350)
                    if percent == 100:
                        await asyncio.gather(chargePoint.stop_transaction(False))
                        state.set_state(States.S_BATTERYFULL)
                        break

                    refreshWindows()
                    time.sleep(1)
                    percent = percent + 1
                    num_of_secs = num_of_secs - 1
                    window_time['ID0'].update(str(m))
                    window_time['ID2'].update(str(s))
                    # update in precents how full the battery currently is
                    # window_chargingPower['TAMER'].update(str(power))
                    window_chargingPercent['PERCENT'].update(str(percent))
                    window_power['POWERTEST'].update(str(percent))

            elif state.get_state() == States.S_BATTERYFULL:

                # hide all the windows below during barttery full image shown on screen
                window_qrCode.hide()
                window_chargingPercent.hide()
                window_chargingPercentMark.hide()
                window_chargingTime.hide()
                window_power.hide()
                window_time.hide()
                window_chargingLastPrice.un_hide()
                window_UsedKWH.un_hide()
                lastPrice = 50
                window_chargingLastPrice['LASTPRICE'].update(str(lastPrice))
                window_back['IMAGE'].update(data=displayStatus.batteryFull())
                refreshWindows()
                await asyncio.sleep(5)
                state.set_state(States.S_AVAILABLE)



