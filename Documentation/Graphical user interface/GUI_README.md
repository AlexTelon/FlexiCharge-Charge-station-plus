# README for graphical user interface tools used in FlexiCharge.


# The project uses PySimpleGUI library as a graphical display tool. [here](https://www.pysimplegui.org/en/latest/)


FlexiCharge project is divided into 4 different classes with different 
characteristics.


## Divison of classes:   
    class Windows(): - Initiate a sg.Windows which constructs and builds a grapical element which can contain text layouts, images etc.
    
    class GUI(): - A class which creates a layout with different elements that the Windows class then initiate and builds into a visual element.

    class Display(): - A class which contains the pathway of which picture should be loaded into its particular layout in the GUI/UI class.

    class UI(): - A class that controls which a particular window should be executed.

## Sequential example of how the graphic user interface it constructed within the code:


__Step 1:__ Construct a layout using PySimpleGUI

    @property
    def start_layout(self):
        self._starting_up_layout =  [[sg.Image(data=Display.starting_up(), 
        key='IMAGE', 
        pad=((0, 0), 
        (0, 0)), 
        size=(480, 800))]]        
        return self._starting_up_layout

 PySimpleGUI constructor for sg.Image - requires a picture to display **Display.starting_up()**, a key word which will be used when the layout is updated **key='IMAGE'** and then finally size constraints.


__Step 2:__ Construct of window using PySimpleGUI

        self._background_window = sg.Window(title="FlexiCharge", 
        layout=self.FLEXI_GUI.start_layout, 
        no_titlebar=True, 
        location=(0, 0), 
        size=(480, 800), 
        keep_on_top=False)

In this case we use the layout of which we constructed in **Step 1**, **FLEX_GUI.start_layout**. We then mimick the same size constraint to avoid any unnecessary bugs.


__Step 3:__
Initiate the background window to be visible:

    # Creates an object of the class Windows called WINDOW_GRAPHICS
    WINDOW_GRAPHICS = Windows()

    def __init__(self):    
             """
            It initialize and builds the window when you run the code.
            """
            self.WINDOW_GRAPHICS._background_window.finalize()

 **.finalize()** confirms that the particular window is now ready to be constructed and displayed.



__Step 4:__ Updating the background window:

- **Example: If the current state is set to  S_NOTAVAILABLE**

        if self.current_state == States.S_NOTAVAILABLE:
                    self.WINDOW_GRAPHICS._background_window['IMAGE'].update(
                        data=Display.charge_not_available())
                    self.WINDOW_GRAPHICS._background_window.refresh()

To update our background window we simply encapsulate the key word **'IMAGE'** which was set in step 1 and call function **.update()** with the correct **Display** image as an input, **Display.charge_not_available()**.

After the update sequence, make sure to refresh the window with the call **.refresh()**

__Step 5:__ 

- **Important note:** When you need to switch between windows, you need to close that particular window which you came from to avoid a duplicate layering issue. 

- **Example:** If your previous state was **S_CHARGING** and you whish to step back to **S_AVAILABLE** you need to hide all windows which is not supposed to be displayed in this current state.

        elif self.current_state == States.S_AVAILABLE:
                   if self.charging_is_done:
                       self.WINDOW_GRAPHICS._charging_last_price_window.hide()
                       self.WINDOW_GRAPHICS._qr_code_window.un_hide() 

To do this, you can use the call function **.hide()**
and also, if you've hidden a window and wish to make it reappear, you can call on the function **.un_hide()**

## This is a simple explanation of how the PySimpleGUI library is used within the code. If you wish to further develop the efficiency of this code, use the link at the top for more in-depth explanation. 
