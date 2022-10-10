import PySimpleGUI as sg
from images import Display


class GUI():

    sg.theme('black')
    
    def __init__(self):
        #Layout variables        
        self._starting_up_layout = None
        self._charging_percent_layout = None        
        self._charging_percent_mark_layout  = None        
        self._qr_code_layout = None        
        self._charging_price_layout = None         
        self._time_layout = None        
        self._last_price = None
        self._used_kwh_layout = None        
        self._power_layout = None        
        self._charging_id = None

    @property
    def start_layout(self):
        self._starting_up_layout =  [[sg.Image(data=Display.starting_up(), key='IMAGE', pad=((0, 0), (0, 0)), size=(480, 800))]]        
        return self._starting_up_layout
    
    @property
    def charging_percent(self): 
        self._charging_percent_layout   =[[ sg.Text("0", font=('ITC Avant Garde Std Md', 160), key='PERCENT', text_color='Yellow')]]       
        return self._charging_percent_layout

    @property
    def charging_percent_mark(self):
        self._charging_percent_mark_layout  =  [[sg.Text("%", font=('ITC Avant Garde Std Md', 55), key='PERCENTMARK', text_color='Yellow')]]
        return self._charging_percent_mark_layout
  
    @property
    def qr_code_layout(self):
        self._qr_code_layout =  [[sg.Image(data=Display.qr_code(), key='QRCODE', size=(285, 285))]]
        return self._qr_code_layout
   
    @property
    def charging_price_layout(self):
        self._charging_price_layout =  [[sg.Text("", font=('Lato', 20), key='PRICE', justification='center', text_color='white'), sg.Text("SEK per KWH", font=('Lato', 20), key='PRICECURRENCY', justification='center', text_color='white')]]
        return self._charging_price_layout

    @property
    def time_layout(self):
        self._time_layout   =[[sg.Text("0", font=('ITC Avant Garde Std Md', 20), key='ID0', text_color='White'), sg.Text("minutes", font=('ITC Avant Garde Std Md', 12), key='ID10', text_color='White'), sg.Text("0", font=('ITC Avant Garde Std Md', 20), key='ID2', text_color='White'), sg.Text("seconds until full", font=('ITC Avant Garde Std Md', 12), key='ID3', text_color='White')]]
        return self._time_layout

    @property
    def last_price(self):
        self._last_price = [[sg.Text("Total Price:", font=('Lato', 20), key='LASTPRICETEXT', justification='center', text_color='white'), sg.Text("", font=('Lato', 20), key='LASTPRICE', justification='center', text_color='white'), sg.Text("SEK", font=('Lato', 20), key='LASTPRICECURRENCY', justification='center', text_color='white')]]
        return self._last_price

    @property
    def used_kwd(self):
        self._used_kwh_layout = [[sg.Text("100 kWh", font=('Lato', 20), key='KWH', justification='center', text_color='white')]]
        return self._used_kwh_layout

    @property
    def power_layout(self):
        self._power_layout =[[sg.Text("", font=('Lato', 20), key='POWERTEST', justification='center', text_color='white'), sg.Text(" kWh", font=('Lato', 20), key='CHARGERPOWERKW', justification='center', text_color='white')]]
        return self._power_layout

   
    #TODO - set charger dynamically
    @property
    def charging_id(self):
        self._charging_id = [[sg.Text(1, font=('Tw Cen MT Condensed Extra Bold', 30), key='ID5', justification='center', pad=(25, 0)),
                              sg.Text(1, font=('Tw Cen MT Condensed Extra Bold', 30), key='ID4', justification='center', pad=(20, 0)),
                              sg.Text(1, font=('Tw Cen MT Condensed Extra Bold', 30), key='ID3', justification='center', pad=(25, 0)),
                              sg.Text(1, font=('Tw Cen MT Condensed Extra Bold', 30), key='ID2', justification='center', pad=(20, 0)),
                              sg.Text(1, font=('Tw Cen MT Condensed Extra Bold', 30), key='ID1', justification='center', pad=(25, 0)),
                              sg.Text(1, font=('Tw Cen MT Condensed Extra Bold', 30), key='ID0', justification='center', pad=(20, 0))]] 

        return self._charging_id