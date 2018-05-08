import os
import atexit
import threading
from time import sleep

#Arduino-Like alias and keywords
OUT = "out"
OUTPUT = OUT
IN = "in"
INPUT = IN
HIGH = True
LOW = False
FALLING = 0
RISING = 1
BOTH = 2

class Pin(object):
    def __init__(self, pin, mode, default_value=False):
        try:
            self.pin = int(pin) #GPIO Pin number
            self.mode = mode #GPIO mode (IN or OUT)
            if self.mode not in (IN, OUT): #Check "mode" param
                raise(self.WrongInput("Pin Mode must be IN or OUT"))
            self.on = True #Is the pin enabled? (ready to use) (exported)
            os.popen("echo {} > /sys/class/gpio/export".format(pin)) #Enable pin (export)
            sleep(0.05)
            if mode == OUTPUT: #If pin is OUTPUT
                HIGHLOW = {True : "high", False : "low"}
                os.popen("echo {} > /sys/class/gpio/gpio{}/direction".format(HIGHLOW[default_value], pin)) #Set initial output value
            else: #If pin is INPUT
                os.popen("echo in > /sys/class/gpio/gpio{}/direction".format(pin))
            sleep(0.05)
            @atexit.register
            def atexit_f(): #Deactivate the pin at exit (unexport)
                self.deactivate()
        except Exception as ex:
            print("Error setting Pin {} as {}:\n{}".format(pin, mode, ex))
    
    def write(self, value):
        """Write a digital value to an OUT pin
        :param value: bool value to write (True/False)
        """
        if self.mode == INPUT:
            raise(self.InvalidOperation("Pin is set as INPUT, not OUTPUT!"))
        try:
            value = int(value)
            os.popen("echo {} > /sys/class/gpio/gpio{}/value".format(value, self.pin))
            sleep(0.025)
        except Exception as ex:
            print("Error setting OUTPUT value on Pin {} as {}\n{}".format(self.pin, value, ex))
    
    def read(self):
        """Read a digital value from an IN pin
        :return: bool value of the pin (True/False)
        """
        if self.mode == OUTPUT:
            raise(self.InvalidOperation("Pin is set as OUTPUT, not INPUT!"))
        try:
            out = os.popen("cat /sys/class/gpio/gpio{}/value".format(self.pin)).read()
            return bool(int(out))
        except Exception as ex:
            print("Error reading value on Pin {}:\n{}".format(self.pin, ex))
    
    def deactivate(self):
        """Free up (unexport) the pin"""
        try:
            if self.on:
                os.popen("echo {} > /sys/class/gpio/unexport".format(self.pin))
                self.on = False
        except:
            pass
    
    def attach_interrupt(self, callback, edge, args=(), frequency=100):
        """Call a function when the pin value changes.
        :param callback: Target function
        :param edge: Interruption edge (FALLING, RISING, BOTH)
        :param args: List of parameters to pass to callback function (Default=empty list)
        :param frequency: Pin value polling frequency in ms
        :return: Interrupt object which has the methods start and stop
        """
        if self.mode == OUTPUT:
            raise(self.InvalidOperation("Pin is set as OUTPUT, not INPUT!"))
        
        class Interrupt(object):
            def __init__(self, pin, callback, edge, frequency):
                """
                :param pin: Pin object
                :param callback: Target function
                :param edge: Interruption edge (FALLING, RISING, BOTH)
                :param frequency: Pin value polling frequency in ms
                """
                self.pin = pin #Pin object
                self.callback = callback
                self.edge = edge
                if self.edge not in (RISING, FALLING, BOTH):
                    raise(ValueError("Edge must be RISING, FALLING or BOTH"))
                self.frequency = frequency #Freq in ms
                self.sleep_value = frequency/1000.0 #Freq in seconds (used by time.sleep)
                self.stopEvent = threading.Event()
            def start(self):
                self.thread = threading.Thread(target=self._thread_f)
                self.thread.daemon = True
                self.stopEvent.clear()
                self.thread.start()
            def stop(self):
                self.stopEvent.set()
            def _thread_f(self):
                before = self.pin.read() #Get initial value
                sleep(self.sleep_value)
                while not self.stopEvent.is_set():
                    now = self.pin.read()
                    if (self.edge == RISING and (not before and now)) or \
                    (self.edge == FALLING and (before and not now)) or \
                    (self.edge == BOTH and (before != now)):
                        self.callback(*args)
                    before = now
                    self.stopEvent.wait(self.sleep_value)
        
        return Interrupt(self, callback, edge, frequency)
    
    class WrongInput(Exception):
        pass
    class InvalidOperation(Exception):
        pass

