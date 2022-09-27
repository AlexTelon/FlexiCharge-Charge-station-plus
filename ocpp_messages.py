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
        """
        It returns a JSON string that contains a list of 4 elements. The first element is an integer,
        the second element is a string, the third element is a string, and the fourth element is a
        dictionary

        :param conversation_id: The conversation ID is a unique identifier for the message. It is used
        to correlate the response to the request
        :return: A JSON string.
        """
        boot_notification_conf = [3,
                    conversation_id,
                    "DataTransfer",
                    {"status": "Accepted"}]
        return boot_notification_conf
