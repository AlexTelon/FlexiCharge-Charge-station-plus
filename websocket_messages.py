import json

class WebSocketMessages:


    def get_boot_notification_req():
        """
        It creates a JSON object that contains the information about the charge point.
        :return: A JSON string
        """
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
        return json.dumps(boot_notification_conf)
    
    