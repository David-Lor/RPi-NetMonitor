
#Native libraries
import subprocess
import threading
import atexit
from datetime import datetime
#Global own modules
from GPIO import *
#Project modules
import outputs

#Settings: Pinout
BUTTON_CPE = 9
BUTTON_WIFI = 10
BUTTON_AUTOREBOOT = 11
BUTTON_INTERRUPT = 24
PIR = 4

#Settings: Timing
BUTTON_HOLD_TIME = 210 #ms
BUTTON_POLLING_FREQ = 150 #ms

#Global variables
autoreboot = True

def switchAutoreboot():
    global autoreboot
    autoreboot = not autoreboot
    outputs.ledAutoreboot.write(autoreboot)

###################################
#### GPIO
###################################

buttonCPE = Pin(BUTTON_CPE, INPUT)
buttonWifi = Pin(BUTTON_WIFI, INPUT)
buttonAutoreboot = Pin(BUTTON_AUTOREBOOT, INPUT)
buttonsInterrupt = Pin(BUTTON_INTERRUPT, INPUT)
pir = Pin(PIR, INPUT)

buttonsTriggers = { #Relation of buttons : function to execute when they're pressed (after HOLD_TIME)
    buttonCPE : outputs.switchCPE,
    buttonWifi : outputs.switchWifi,
    buttonAutoreboot : switchAutoreboot
}

def getPIR():
    return pir.read()

###################################
#### Pushbuttons
###################################

stopEvents = list()

def _interruptService():
    def _buttonService(button, stopEvent):
        stopEvent.wait(BUTTON_HOLD_TIME/1000)
        if not stopEvent.is_set() and button.read():
            f = buttonsTriggers[button]
            print("Button at pin", button.pin, "pressed executing", f)
            f()
        else:
            print("Button at pin", button.pin, "released before HoldTime")
    try:
        button = next(b for b in buttonsTriggers.keys() if b.read())
    except StopIteration:
        return
    print("Pressed button at pin", button.pin)
    stopEvent = threading.Event()
    stopEvents.append(stopEvent)
    th = threading.Thread(
        target=_buttonService,
        daemon=True,
        args=(button, stopEvent)
    )
    th.start()

interrupt = buttonsInterrupt.attach_interrupt(
    callback=_interruptService,
    edge=RISING,
    frequency=BUTTON_POLLING_FREQ
)
interrupt.start()

@atexit.register
def atexit_f():
    interrupt.stop()
    for event in stopEvents:
        event.set()

###################################
#### Other Getters
###################################

def getLinkStatus():
    """Get network link status (if net iface is UP, i.e. LAN cable attached)
    :return: True if UP, False if DOWN
    """
    return bool(int(subprocess.check_output(("cat", "/sys/class/net/eth0/carrier"))))

def getAutorebootStatus():
    return autoreboot
