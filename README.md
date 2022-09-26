# FlexiCharge-Charge-station-plus

### Raspberry Pi Touchscreen Setup

According to the Picture below.
------------------------------
GND is black wire to the third pin down on the right-hand side.
5V is red wire to the second pin down on the right.
SCL is yellow wire to the third pin down on the left-hand side.
SDA is green wire to the second pin down on the left-hand side.

To connect the white ribbon cable supplied, connect one end to the controller board, make sure that this end has the blue tab facing down, towards the board (the opposite end, the end not being attached to the controller board, should have the blue tab facing up, so you can see it. Picture below.

<img width="393" alt="Capture" src="https://user-images.githubusercontent.com/82366694/186842602-1ed6600e-4e68-4280-a87a-749ac07913f9.PNG">

### PysimpleGUI

1- The used library is pysimpleGUI so you need to install the following commands on the terminal.
------------------------------------------------------------------------------------------------
pip3 install pysimplegui <br />
pip3 install pillow

2- You need to install the following command on the termina to use the qr code generator.
----------------------------------------------------------------------------------------
pip3 install qrcode 

3- You need to install the following command on the termina to use the websockets
------------------------------------------------------------------------------------------------
pip3 install websockets

### How to run the program:
To run the program, open PowerShell (for Windows) or Terminal (for Linux) and navigate to FlexiCharge-Charge-station-plus -> ChargeStation and enter python3 state-machine.py

### What should happen?

1. A start-up screen will first be shown.
2. Then, if the connection was successfully established, a QR-code and an ID-number will show up. Otherwise an error message will show up if the ChargePoint wasn’t able to connect to the server.
3. Connect to the charger via the app and the charger should ask you to follow the instructions in the app.
4. Go through the payment in the app, then the charger should start charging.
5. The user continue to charge until it's fully charged, the screen will display 100% and the price should be shown in 5 seconds. If the user cancel the charging, the charger will go back to the QR-code/ID-number screen. 

### Good to know: 
"images.py" include all images from zeplin(think about the path of the images if you get error), "StateHandler" include Enum for all the states, and "state-machine" include the main code and state-machine.

To start the OCPP-mock server launch a new terminal on you PC and go into the flexicharge-charge-plus REPO then execute the python file.
Example: python3 .\ocpp_mock_server.py 
After this, when you start the state machine and connect to the "server" the terminal should print the boot message request and boot message response.

### Development Requirements:
Python 3.9 <br />
Visual Studio Code
