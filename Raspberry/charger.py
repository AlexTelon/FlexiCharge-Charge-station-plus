#Import the required Libraries
from tkinter import *
from PIL import Image,ImageTk

#Variables
chargerId : int
location : int
chargerPointId : int
status : enumerate

#Create an instance of tkinter frame
win = Tk()

#Set the geometry of tkinter frame
win.geometry("480x800")

#Create a canvas
canvas= Canvas(win, width= 200, height= 400)
canvas.pack()

#Load an image in the script
img= (Image.open("busy.png"))

#Resize the Image using resize method
resized_image= img.resize((200,350), Image.ANTIALIAS)
new_image= ImageTk.PhotoImage(resized_image)

#Add image to the Canvas Items
canvas.create_image(10,10, anchor=NW, image=new_image)
chargerId = 123456
myLable = Label(win, text = chargerId,
                        foreground="red",
                        font = (None,25))
myLable.pack()

win.mainloop()