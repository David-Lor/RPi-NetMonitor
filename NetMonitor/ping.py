
#Native libraries
import random
import subprocess
import atexit
from time import sleep
#Project modules
from inputs import getLinkStatus, getAutorebootStatus, getPIR
from outputs import rebootCPE, lcdWrite, ledPing

#Settings: Ping
PING_MAXERRORS = 4
PING_LOOP_FREQ = 3
PING_LCD_ROTATION_FREQ = 1

#Global variables
pingErrors = 0

###################################
#### Servers to ping and functions
###################################

servers = list() #List of tuples (server ip, server description)

with open("NetMonitor/SERVERS.txt","r") as file:
    for line in file.readlines():
        if line == "" or not "," in line or line[0] == "#":
            continue #ignore empty lines or commented lines
        line = line.strip().split(",")
        servers.append((line[0], line[1]))

if len(servers) < 2:
    print("NO ENOUGH SERVERS SPECIFIED IN SERVERS.txt")
    print("We need at least 2 servers to ping")
    exit()

lastServerIndex = None

def getserver():
    """Return a random server from servers list.
    The server is alweays different than the last server returned.
    :return: tuple (server ip, server description)
    """
    global lastServerIndex
    serverIndex = lastServerIndex
    while serverIndex == lastServerIndex:
        serverIndex = random.randint(0, len(servers)-1)
    lastServerIndex = serverIndex
    return servers[serverIndex]

def ping(server):
    """Ping a server.
    :return: avg latency in ms (float) or False if ping was unsuccessful
    """
    r = subprocess.run(("./ping.sh", server), stdout=subprocess.PIPE)
    if r.returncode > 0:
        return False
    return float(r.stdout)

###################################
#### Loop
###################################

@atexit.register
def atexit_f():
    lcdWrite("**clearscreen**")

def loop():
    global pingErrors

    server = getserver()
    serverIP = server[0]
    serverName = server[1]
    result = ping(serverIP)
    lcdA = [serverIP, serverName]

    #Ping OK
    if type(result) is float:
        pingErrors = 0
        lcdB = "{0:.3f} ms".format(result)
        ledPing.write(True)
    
    #Ping KO
    else:
        ledPing.write(False)

        if getLinkStatus(): #LAN cable is linked up
            pingErrors += 1
            if getAutorebootStatus() and pingErrors >= PING_MAXERRORS: #We must reboot CPE
                rebootCPE()
                pingErrors = 0
                sleep(PING_LOOP_FREQ)
                return
            #If max errors not reached, generate line B for LCD
            lcdB = "DOWN - Err: {}/{}".format(pingErrors, PING_MAXERRORS)
            if len(lcdB) > 16: #Short line B string
                lcdB = lcdB.replace(" ","")
        
        else: #LAN cable is disconnected
            lcdB = "LINK DOWN"
    
    #Print LCD
    if getPIR():
        lcdWrite(
            lineA=lcdA,
            lineB=lcdB,
            rotateFreq=PING_LCD_ROTATION_FREQ
        )
    else:
        lcdWrite("**clearscreen**")
    
    #Sleep/Loop delay
    sleep(PING_LOOP_FREQ)
