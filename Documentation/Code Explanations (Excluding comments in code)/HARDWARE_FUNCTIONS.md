# Hardware functions guide

This is a description of how the hardware functions work

## RFID Functions

For the RFID functions to work on the Raspberry Pi we import these <br />

    if platform.system() == 'Linux': 
        import RPi.GPIO as GPIO
        from mfrc522 import SimpleMFRC522 

Why we have the if-statement above the imports are because they can only be downloaded on a Linux based machine. So, we don't want to import them unless we are on a linux machine. <br/>

### RFID read function

The first thing we do is a __SimpleMFRC522__ object called reader.

        reader = SimpleMFRC522()

Then we have the code that actually reads the RFID-tag. 

         try:
            idToken, text = reader.read()
         finally:
            GPIO.cleanup()

The read()-function assigns the idToken and text variables. idToken gets the id from det RFID-tag and if there is a text written to the tag the text variable will get that. <br/>
GPIO.cleanup() will reset the GPIO-pins you used in the program to input mode. 

### RFID write function 
This function is pretty much the same as read except that it writes to the RFID-tag with this code:

     try:
        text = input("New Data: ")
        print("Place tag to write")
        reader.write(text)
        print("written")

The text variable takes a user input that says what the write()-function should write on the RFID-tag. 
