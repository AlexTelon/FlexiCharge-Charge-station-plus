import json

class WebSocketMessages:
    def get_boot_notification_req():
        send_boot_notification = [2, "0jdsEnnyo2kpCP8FLfHlNpbvQXosR5ZNlh8v", "BootNotification", {
                "chargePointVendor": "AVT-Company",
                "chargePointModel": "AVT-Express",
                "chargePointSerialNumber": "avt.001.13.1",
                "chargeBoxSerialNumber": "avt.001.13.1.01",
                "firmwareVersion": "0.9.87",
                "iccid": "",
                "imsi": "",
                "meterType": "AVT NQC-ACDC",
                "meterSerialNumber": "avt.001.13.1.01"}]
        return json.dumps(send_boot_notification)
    def get_boot_notification_conf(conversation_id):
        boot_notification_conf = [3,
                    conversation_id,
                    "DataTransfer",
                    {"status": "Accepted"}]
        return json.dumps(boot_notification_conf)