import io
from PIL import Image

def get_img_data(f, maxsize=(480, 800)):
    img = Image.open(f)
    img.thumbnail(maxsize)
    bio = io.BytesIO()
    img.save(bio, format="PNG")
    del img
    return bio.getvalue()

class Display:
    def charge_not_available():
        img_charge_not_available = get_img_data('charger_images/chargeNotAvailable.png')
        return img_charge_not_available
    def charging_id():
        img_qr_code = get_img_data('charger_images/chargingID.png')
        return img_qr_code
    def authorizing():
        img_authorizing = get_img_data('charger_images/AuthorizingTag.png')
        return img_authorizing
    def battery_full():
        img_battery_full = get_img_data('charger_images/BatteryFull.png')
        return img_battery_full
    def charging():
        img_charging = get_img_data('charger_images/Charging.png')
        return img_charging
    def charging_cancelled():
        img_charging_cancelled = get_img_data('charger_images/ConnectingToCar.png')
        return img_charging_cancelled
    def disconnecting_from_car():
        img_disconnecting_from_car = get_img_data('charger_images/DisconnectingFromCar.png')
        return img_disconnecting_from_car
    def charging_error():
        img_charging_error = get_img_data('charger_images/errorOccuredWhileCharging.png')
        return img_charging_error
    def flexi_charge_app():
        img_flexi_charge_app = get_img_data('charger_images/FlexiChargeApp.png')
        return img_flexi_charge_app
    def connecting_to_car():
        img_connecting_to_car = get_img_data('charger_images/ConnectingToCar.png')
        return img_connecting_to_car
    def plug_cable():
        img_plug_cable = get_img_data('charger_images/PlugInTheCable.png')
        return img_plug_cable
    def starting_up():
        img_starting_up = get_img_data('charger_images/startingUp.png')
        return img_starting_up
    def tag_not_valid():
        img_tag_not_valid = get_img_data('charger_images/tagNotValid.png')
        return img_tag_not_valid
    def unable_to_charge():
        img_unable_to_charge = get_img_data('charger_images/unableToCharge.png')
        return img_unable_to_charge
    def qr_code():
        img_qr_code = get_img_data('charger_images/qrCode.png')
        return img_qr_code
    