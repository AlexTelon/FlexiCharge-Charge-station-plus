import json

class OCPPMessages:

    boot_notification_conf = [2, "", "BootNotification", {
                "chargePointVendor": "AVT-Company",
                "chargePointModel": "AVT-Express",
                "chargePointSerialNumber": "avt.001.13.1",
                "chargeBoxSerialNumber": "avt.001.13.1.01",
                "firmwareVersion": "0.9.87",
                "iccid": "",
                "imsi": "",
                "meterType": "AVT NQC-ACDC",
                "meterSerialNumber": "avt.001.13.1.01"}]
        
    def get_boot_notification_conf(conversation_id):
        boot_notification_conf = [3,
                    conversation_id,
                    "DataTransfer",
                    {"status": "Accepted"}]
        return boot_notification_conf