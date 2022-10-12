# Websocket developer guide
This is a description of how the charger is using the websockets to achieve communication with the __OCPP__ interface.

## Initializing the websocket
We initialize the websocket class inside the main function of the state_machine file.<br />
It looks something like below.

    async def main():
        try:
            webSocket = WebSocket()
            await(statemachine(webSocket))

        except Exception as e:
            print("ERROR:")
            print(e)

### __This is the order that things progress__
#### 1. **An object of the websocket class is initialized.**
#### 2. **The state machines is started**

Lets dive a bit deeper into the second step to find what is actually going on under the hood.

__In step 1 where:__

     webSocket = WebSocket()
Is called the corresponding __init__ function is run in the __WebSocket()__ class

    def __init__(self):
            try:
                print("ws_init")
                self._webSocket = None

            except Exception as e:
                self._webSocket = None
                print("ws_init_failed")
                print(str(e))
This creates a member variable called _webSocket that will later be filled in by the actual websocket but right now it is just a **None** type object.


__In step 2 where:__

    await webSocket.start_websocket()
Is called. This creates the connection to the websocket server and is the start of the communication.<br /> I will describe the following function below:

    async def start_websocket(self):
            """
            It tries to connect to a websocket, if it succeeds it sends a boot notification request.
            :return: The return value is a coroutine object.
            """
            try:
                async with ws.connect(
                    Config().getServerAddress(),
                    subprotocols=Config().getProtocol(),
                    ping_interval=Config().getWebSocketPingInterval(),
                    timeout=Config().getWebSocketTimeout()
                ) as webSocketConnection:
                    self._webSocket = webSocketConnection
                    print("Successfully connected to WebSocket")
                    await self.send_boot_notification_req()
                    while (True):
                        print("Reading ws")
                        message = await self._webSocket.recv()
                        message_json = json.loads(message)
                        await self.handle_message(message_json)

            except Exception as e:
                CHARGER_VARIABLES.current_state = States.S_NOTAVAILABLE
                print("connect failed")
                print(str(e))
### __The initiation runs like this__
#### 1. **Insert the configuration variables into the connect function and save the connection as webSocketConnection**
#### 2. **Assign the webSocketConnection to the local _webSocket variable**
#### 3. **Run the boot notification request to start the communication between our client and the OCPP Server**
#### 4. **Keep the connection alive and recieve messages using a while true loop that checks for new messages from the server and sends the messages into the self.handle_message function**
<br />

**In step 1:**

    async with ws.connect(
                        Config().getWebSocketAddress(),
                        subprotocols=Config().getProtocol(),
                        ping_interval=Config().getWebSocketPingInterval(),
                        timeout=Config().getWebSocketTimeout()
                    ) as webSocketConnection:
 
 We begin by accessing the __config.py__ to get all the variables that are nessecary to connect to the __OCPP__ server. <br/>
 For a more detailed description of the input variables visit the Python websockets site [here](https://websockets.readthedocs.io/en/stable/reference/client.html) <br />

 **In step 2:**

    self._webSocket = webSocketConnection
    print("Successfully connected to WebSocket")

We assign the webSocketConnection to the _webSocket variable and print out that the connection has succeeded.

**In step 3:**

    await self.send_boot_notification_req()

We run the boot notification request function to start the conversation with the __OCPP__ server.

## Sending the boot notification
We send a __Boot Notification__ to the __OCPP__ Server to let them know that we are booting up and to give them some information about the charger.<br />

**The function used for sending a boot notification request looks like this**

    async def send_boot_notification_req(self):
            msg = [2, "0jdsEnnyo2kpCP8FLfHlNpbvQXosR5ZNlh8v", "BootNotification", {
                "chargePointVendor": "AVT-Company",
                "chargePointModel": "AVT-Express",
                "chargePointSerialNumber": "avt.001.13.1",
                "chargeBoxSerialNumber": "avt.001.13.1.01",
                "firmwareVersion": "0.9.87",
                "iccid": "",
                "imsi": "",
                "meterType": "AVT NQC-ACDC",
                "meterSerialNumber": "avt.001.13.1.01"}]
            msg_send = json.dumps(msg)
            print("Sending boot notification")
            await self.send_message(msg_send)

### **Here three things are happening**
#### 1. We create a standard boot notification message containing all the nessecary information for the OCPP server.
    msg = [2, "0jdsEnnyo2kpCP8FLfHlNpbvQXosR5ZNlh8v", "BootNotification", {
                "chargePointVendor": "AVT-Company",
                "chargePointModel": "AVT-Express",
                "chargePointSerialNumber": "avt.001.13.1",
                "chargeBoxSerialNumber": "avt.001.13.1.01",
                "firmwareVersion": "0.9.87",
                "iccid": "",
                "imsi": "",
                "meterType": "AVT NQC-ACDC",
                "meterSerialNumber": "avt.001.13.1.01"}]

To describe the message syntax it usually goes like this.

    [Send or Answer(2/3),
     UniqueID (In this case a hard coded string but usually following the format chargerId+MessageType+Timestamp in milliseconds since UNIX time),
     Message type,{data}]
#### 2. We transform the message to a json formatted string
    msg_send = json.dumps(msg)
#### 3. We send the string
Here we are utilizing a function we wrote called __send_message()__

    await self.send_message(msg_send)


**In step 4:**


## Receiving messages from OCPP
Now that we have sent a boot notification the next thing to happen is that we should receive a __DataTransfer__ message from the __OCPP__ server.

The __DataTransfer__ message will contain information that we need to run our application. The two most vital things are __chargerId__ and __chargingPrice__.<br />
The __chargerId__ is the id for our specific charger and it is needed to create the qr code that is displayed in the **Available** state. <br />
It is also used to create __unique ids__ for the conversations with the __OCPP__ server.

### Here are some different messages that you will receive from the __OCPP__ server

#### - ReserveNow
    [3, "UNIQUE ID","ReserveNow",{"status": "Accepted"}]
Reserve now is a pretty standard confirmation message. Which means that it is built on 4 different databoxes. <br/>
__Index 0__ Means that we are answering a call since it is a 3. <br/>
__Index 1__ Is a unique id. When we are answering a call we need to answer with the __same id__ that the server sent us. Therefor we save the message they sent us and use their unique id in our answer.<br/>
__Index 2__ This box contains the message type. So in this case just __ReserveNow__ <br/>
__Index 3__ This box contains __Data__ to be transfered to the __OCPP__ server it is structured up like this:<br/>
__{ "datatype" : "DATA"}__ <br/>
If you want to send more than one type of data you can do it like this! <br/>
__{ "datatype" : "DATA" , <br/>
    "some_other_datatype" : "OTHERDATA"}__

Then when you send it to the server you need to do the following line.

    message = [3, "UNIQUE ID","ReserveNow",{"status": "Accepted"}]
    json_formatted_message = json.dumps(message)
    self.send_message(json_formatted_message)
