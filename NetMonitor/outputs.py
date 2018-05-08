
#Native libraries
import threading
from time import sleep
#Installed libraries
import paho.mqtt.client as mqtt
#Global own modules
from GPIO import *

#Settings: Pinout
LED_PING = 25
LED_AUTOREBOOT = 8
RELAY_CPE = 22
RELAY_WIFI = 27

#Settings: Timing
REBOOT_OFF_TIME = 15 #Time to wait when CPE/WIFI turned off, before turning it on again
REBOOT_WAIT_TIME = 75 #Time to wait after CPE rebooted, before start pinging again

#Settings: LCD
MQTT_LCD_TOPIC = "$lcd"

###################################
#### MQTT LCD
###################################

mqttClient = mqtt.Client()
mqttClient.connect("localhost")

def lcdWrite(lineA="", lineB="", priority=100, minTime=0, maxTime=0, rotateFreq=0.5, autoclear=1, center=1):
    payload = {
        "lineA" : lineA,
        "lineB" : lineB,
        "priority" : priority,
        "min_time" : minTime,
        "max_time" : maxTime,
        "rotate_freq" : rotateFreq,
        "autoclear" : int(autoclear),
        "center" : int(center)
    }
    payload = str(payload).replace("'", '"')
    mqttClient.publish(MQTT_LCD_TOPIC, payload)

#test print
#lcdWrite("Network Monitor",["Is running","LCD test string","nothing to do"])

###################################
#### GPIO (LEDs + Relays)
###################################

ledPing = Pin(LED_PING, OUTPUT, LOW)
ledAutoreboot = Pin(LED_AUTOREBOOT, OUTPUT, HIGH)
relayCPE = Pin(RELAY_CPE, OUTPUT, HIGH) #Relays are actived with LOW
relayWifi = Pin(RELAY_WIFI, OUTPUT, HIGH) #Relay actived = device OFF

cpeStatus, wifiStatus = True, True #devStatus=True means device is (can be) ON

def blink(led, freq, stopEvent):
    st = False
    while not stopEvent.isSet():
        st = not st
        led.write(st)
        stopEvent.wait(freq)
    led.write(LOW)

def setCPE(value):
    global cpeStatus
    relayCPE.write(value)
    cpeStatus = value

def switchCPE():
    setCPE(not cpeStatus)

def setWifi(value):
    global wifiStatus
    relayWifi.write(value)
    wifiStatus = value

def switchWifi():
    setWifi(not wifiStatus)

def getCPEStatus():
    return cpeStatus

def getWifiStatus():
    return wifiStatus

def _rebootDevice(devSetFunction, devStatus, devName, offTime, waitTime):
    if devStatus:
        devSetFunction(False)
        lcdWrite(
            #lineA="REBOOTING " + devName,
            #lineA="REINICIANDO " + devName,
            lineA="REINICIANDO {}".format(devName),
            lineB="",
            priority=200,
            autoclear=False
        )
        
        for i in reversed(range(offTime+1)):
            lcdWrite(
                lineA="**ignore**",
                #lineB="Turn on in {}s".format(i),
                lineB="Encender en {}s".format(i),
                priority=200,
                autoclear=False
            )
            if i != 0:
                sleep(1)
        
        devSetFunction(True)
        lcdWrite(
            #lineA=devName + " REBOOTED",
            #lineA=devName + " REINICIADO",
            lineA="{} REINICIADO".format(devName),
            lineB="",
            priority=200,
            autoclear=False
        )
        
        if waitTime:
            for i in reversed(range(waitTime+1)):
                lcdWrite(
                    lineA="**ignore**",
                    #lineB="Wait {}s".format(i),
                    lineB="Espera {}s".format(i),
                    priority=200,
                    autoclear=False
                )
                if i != 0:
                    sleep(1)
        
        lcdWrite(
            lineA="**ignore**",
            lineB="OK!",
            priority=201,
            minTime=0.1
        )

def rebootCPE(offTime=REBOOT_OFF_TIME, waitTime=REBOOT_WAIT_TIME):
    blinkStopEvent = threading.Event()
    blinkThread = threading.Thread(
        target=blink,
        args=(ledPing, 0.4, blinkStopEvent),
        daemon=True
    )
    blinkThread.start()
    _rebootDevice(
        devSetFunction=setCPE,
        devStatus=cpeStatus,
        devName="CPE",
        offTime=offTime,
        waitTime=waitTime
    )
    blinkStopEvent.set()

def rebootWifi(offTime=REBOOT_OFF_TIME, waitTime=0):
    _rebootDevice(
        devSetFunction=setWifi,
        devStatus=wifiStatus,
        devName="WIFI",
        offTime=offTime,
        waitTime=waitTime
    )

