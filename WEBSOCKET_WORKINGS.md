# Websocket developer guide
This is a description of how the charger is using the websockets to achieve communication with the __OCPP__ interface.

## Initializing the websocket
We initialize the websocket class inside the main function of the state_machine file.<br />
It looks something like below.

    async def main():
        try:
            webSocket = WebSocket()
            await webSocket.initiate_websocket()
            asyncio.get_event_loop().run_until_complete(await statemachine(webSocket))

        except Exception as e:
            print("ERROR:")
            print(e)

### __This is the order that things progress__
### 1. **The websocket is initialized as an object.**
### 2. **The initiate_websocket() function is called**
### 3. **Run the state machine until complete.**

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

    await webSocket.initiate_websocket()
Is called. This creates the connection to the websocket server and is the start of the communication.<br /> I will describe the following function below:

    async def initiate_websocket(self):
            try:
                async with ws.connect(
                    Config().getWebSocketAddress(),
                    subprotocols=Config().getProtocol(),
                    ping_interval=Config().getWebSocketPingInterval(),
                    timeout=Config().getWebSocketTimeout()
                ) as webSocketConnection:
                    self._webSocket = webSocketConnection
                    print("Successfully connected to WebSocket")
                    await self.send_boot_notification_req()
            except Exception as e:
                print("connect failed")
                print(str(e))
### __The initiation runs like this__
### 1. **Insert the configuration variables into the connect function and save the connection as webSocketConnection**
### 2. **Assign the webSocketConnection to the local _webSocket variable**
### 3. **Run the boot notification request to start the communication between our client and the OCPP Server**
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
### 1. We create a standard boot notification message containing all the nessecary information for the OCPP server.
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
### 2. We transform the message to a json formatted string
    msg_send = json.dumps(msg)
### 3. We send the string
Here we are utilizing a function we wrote called __send_message()__

    await self.send_message(msg_send)
    