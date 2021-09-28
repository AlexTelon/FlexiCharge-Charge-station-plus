from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from _typeshed import Self
import io
from PIL import Image
import os

def get_img_data(f, maxsize=(480, 800)):
    img = Image.open(f)
    img.thumbnail(maxsize)
    bio = io.BytesIO()
    img.save(bio, format="PNG")
    del img
    return bio.getvalue()



class displayStatus:
    dirname = os.path.dirname(__file__)


    def chargeNotAvailable():
        dirname = os.path.dirname(__file__)
        filename = os.path.join(dirname, 'charger_images/chargeNotAvailable.png')
        img_chargeNotAvailable = get_img_data(filename)
        return img_chargeNotAvailable

    def qrCode():
        dirname = os.path.dirname(__file__)
        filename = os.path.join(dirname, 'charger_images/QRcode.png')
        img_qrCode = get_img_data(filename)
        return img_qrCode

    def authorizing():
        dirname = os.path.dirname(__file__)
        filename = os.path.join(dirname, 'charger_images/AuthorizingTag.png')
        img_authorizing = get_img_data(filename)
        return img_authorizing

    def batteryFull():
        dirname = os.path.dirname(__file__)
        filename = os.path.join(dirname, 'charger_images/BatteryFull.png')
        img_batteryFull = get_img_data(filename)
        return img_batteryFull

    def charging():
        dirname = os.path.dirname(__file__)
        filename = os.path.join(dirname, 'charger_images/Charging.png')
        img_charging = get_img_data(filename)
        return img_charging

    def chargingCancelled():
        dirname = os.path.dirname(__file__)
        filename = os.path.join(dirname, 'charger_images/ConnectingToCar.png')
        img_chargingCancelled = get_img_data(filename)
        return img_chargingCancelled

    def disconnectingFromCar():
        dirname = os.path.dirname(__file__)
        filename = os.path.join(dirname, 'charger_images/DisconnectingFromCar.png')
        img_disconnectingFromCar = get_img_data(filename)
        return img_disconnectingFromCar

    def chargingError():
        dirname = os.path.dirname(__file__)
        filename = os.path.join(dirname, 'charger_images/errorOccuredWhileCharging.png')
        img_chargingError = get_img_data(filename)
        return img_chargingError

    def flexiChargeApp():
        dirname = os.path.dirname(__file__)
        filename = os.path.join(dirname, 'charger_images/FlexiChargeApp.png')
        img_flexiChargeApp = get_img_data(filename)
        return img_flexiChargeApp

    def connectingToCar():
        dirname = os.path.dirname(__file__)
        filename = os.path.join(dirname, 'charger_images/ConnectingToCar.png')
        img_connectingToCar = get_img_data(filename)
        return img_connectingToCar

    def plugCable():
        dirname = os.path.dirname(__file__)
        filename = os.path.join(dirname, 'charger_images/PlugInTheCable.png')
        img_plugCable = get_img_data(filename)
        return img_plugCable

    def startingUp():
        dirname = os.path.dirname(__file__)
        filename = os.path.join(dirname, 'charger_images/startingUp.png')
        img_startingUp = get_img_data(filename)
        return img_startingUp

    def tagNotValid():
        dirname = os.path.dirname(__file__)
        filename = os.path.join(dirname, 'charger_images/tagNotValid.png')
        img_tagNotValid = get_img_data(filename)
        return img_tagNotValid

    def unableToCharge():
        dirname = os.path.dirname(__file__)
        filename = os.path.join(dirname, 'charger_images/unableToCharge.png')
        img_unableToCharge = get_img_data(filename)
        return img_unableToCharge
    