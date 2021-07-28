# Domoticz WiZ connected Plugin
#
# Author: Syds Post sydspost@gmail.com
#
"""
<plugin key="wiz" name="WiZ connected" author="Syds Post" version="1.0.0" wikilink="" externallink="https://www.wizconnected.com/">
    <description>
        <h2>WiZ connected Plugin</h2><br/>
        This plugin is meant to control WiZ connected devices. WiZ connected devices may come with different brands as Philips, TAO and WiZ connected etc.
        <h3>Features</h3>
        <ul style="list-style-type:square">
            <li>Auto-detection of devices on network</li>
            <li>On/Off control, state and available status display</li>
            <li>Dimmer/Warm-cold setting for Lights</li>
<!--            <li>Scene activation support</li> -->
        </ul>
        <h3>Devices</h3>
        <ul style="list-style-type:square">
            <li>All devices that have on/off state should be supported</li>
        </ul>
        <h3>Configuration</h3>
        Devices can be renamed in Domoticz or you can rename them in the App and remove them from Domoticz so they are detected with a new name or layout.
        Be careful when setting the subnet, setting class A or class B networks can lead to performance issues because the plugin uses ARP ping
        to detect the WiZ connected devices. Hostname Prefix is a comma seperated list of the first 4 characters of the hostname of the WiZ connected devices per brand.
    </description>
    <params>
        <param field="Mode1" label="Hostname Prefix" width="200px" required="true" default="wiz_"/>
        <param field="Mode2" label="Subnet" width="200px" required="true" default="192.168.2.0/24"/>
        <param field="Mode6" label="Debug" width="150px">
            <options>
                <option label="None" value="0"  default="true" />
                <option label="Python Only" value="2"/>
                <option label="Basic Debugging" value="62"/>
                <option label="Basic+Messages" value="126"/>
                <option label="Connections Only" value="16"/>
                <option label="Connections+Python" value="18"/>
                <option label="Connections+Queue" value="144"/>
                <option label="All" value="-1"/>
            </options>
        </param>
    </params>
</plugin>
"""
import Domoticz
import threading
import socket
import html
import sys
import time
import math
import json
import re
from scapy.all import srp,Ether,ARP,conf

class BasePlugin:
    startup = True;
    devs = {}
    last_update = 0

    def __init__(self):
        return

    def onStart(self):
        Domoticz.Log("WiZ connected plugin started")
        if Parameters["Mode6"] != "0":
            Domoticz.Debugging(int(Parameters["Mode6"]))
            DumpConfigToLog()

        # Find devices that already exist, create those that don't
        conf.verb=0
        ans,unans=srp(Ether(dst="ff:ff:ff:ff:ff:ff")/ARP(pdst=Parameters["Mode2"]), timeout=2)

        hostNames = []

        for snd,rcv in ans:
            ipAddress=rcv.sprintf(r"%ARP.psrc%")
            try:
                hostName = socket.gethostbyaddr(ipAddress)
            except:
                hostName = "Onbekend"

            if hostName[0].startswith(Parameters["Mode1"]):
                hostNames.append(hostName[0])
    
        for hostName in hostNames:
            Domoticz.Debug("Endpoint '"+hostName+"' found.")
            deviceFound = False
            for Device in Devices:
                if ((hostName == Devices[Device].DeviceID)): deviceFound = True
            if (deviceFound == False):
                Domoticz.Device(Name=hostName, DeviceID=hostName,  Unit=len(Devices)+1, Type=241, Subtype=8, Switchtype=7, Image=0).Create()


    def onStop(self):
        Domoticz.Debug("onStop called")
        while (threading.active_count() > 1):
            time.sleep(1.0)

    def onConnect(self, Connection, Status, Description):
        Domoticz.Debug("onConnect called")

    def onMessage(self, Connection, Data):
        Domoticz.Debug("onMessage called")

    def onCommand(self, Unit, Command, Level, Color):
        Domoticz.Debug("onCommand called for Unit " + str(Unit) + ": Parameter '" + str(Command) + "', Level: " + str(Level))

        # Find the device for the Domoticz Unit provided
        dev = None
        try:
            dev = Devices[Unit] 
        except Exception as e:
            Domoticz.Debug("Device has no ID " + str(Unit) + " " + str(e))

        # If we didn't find it, leave (probably disconnected at this time)
        if dev == None:
            Domoticz.Error('Command for DeviceID='+Devices[Unit].DeviceID+' but device is not available.')
            return

        # if not dev.available():
        #     Domoticz.Error('Command for DeviceID='+Devices[Unit].DeviceID+' but device is offline.')
        #     return

        Domoticz.Log('Sending command for DeviceID='+Devices[Unit].DeviceID)
        host = str(Devices[Unit].DeviceID)
        port = 38899

        # Control device and update status in Domoticz
        if Command == 'On':
            mJSON = b'{"method":"setPilot","params":{"src":"udp","state":true}}'
            sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            try:
                sock.sendto(mJSON, (host, port))
 
                received = sock.recv(1024)
            finally:
                sock.close()

            received=str(received).split(",")[2].split(":")[2]
            received=received[0:len(received)-3].capitalize()

            UpdateDevice(Unit, 1, 'On', not received)
        elif Command == 'Off':
            mJSON = b'{"method":"setPilot","params":{"src":"udp","state":false}}'
            sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            try:
                sock.sendto(mJSON, (host, port))

                received = sock.recv(1024)
            finally:
                sock.close()

            received=str(received).split(",")[2].split(":")[2]
            received=received[0:len(received)-3].capitalize()

            UpdateDevice(Unit, 0, 'Off', not received)
        elif Command == 'Set Color':
            # Convert RGB to Cold- and White level
            rgb = json.loads(Color)
            mode = rgb.get("m")
            cw = rgb.get("cw")
            ww = rgb.get("ww")

            mJSON = bytes('{"method":"setPilot","params":{"src":"udp","state":true,"c":' + str(cw) + ',"w":' + str(ww) + '}}', 'utf-8')
            sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            try:
                sock.sendto(mJSON, (host, port))

                received = sock.recv(1024)
            finally:
                sock.close()

            received=str(received).split(",")[2].split(":")[2]
            received=received[0:len(received)-3].capitalize()

            # Update status of Domoticz device
            Devices[Unit].Update(nValue=1, sValue=str(Level), TimedOut=not received, Color=Color)
        elif Command == 'Set Level':
            # Set new level
            mJSON = bytes('{"method":"setPilot","params":{"src":"udp","state":true,"dimming":' + str(Level) + '}}', 'utf-8')
            sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            try:
                sock.sendto(mJSON, (host, port))

                received = sock.recv(1024)
            finally:
                sock.close()

            received=str(received).split(",")[2].split(":")[2]
            received=received[0:len(received)-3].capitalize()

            # Update status of Domoticz device
            UpdateDevice(Unit, 1 if Devices[Unit].Type == 241 else 2, str(Level), not received)

        # Set last update
        self.last_update = time.time()

    def onNotification(self, Name, Subject, Text, Status, Priority, Sound, ImageFile):
        Domoticz.Debug("Notification: " + Name + "," + Subject + "," + Text + "," + Status + "," + str(Priority) + "," + Sound + "," + ImageFile)

    def onDisconnect(self, Connection):
        Domoticz.Debug("onDisconnect called")

    def onHeartbeat(self):
        Domoticz.Debug("onHeartbeat called time="+str(time.time()))
        # If it hasn't been at least 1 minute (corrected for ~2s runtime) since last update, skip it
        # if time.time() - self.last_update < 58:
        #     return
        self.startup = False
        # Create/Start update thread
        self.updateThread = threading.Thread(name="WiZUpdateThread", target=BasePlugin.handleThread, args=(self,))
        self.updateThread.start()

    # Separate thread looping ever 10 seconds searching for new WiZ connected devices on network and updating their status
    def handleThread(self):
        try:
            Domoticz.Debug("in handlethread")
            # Initialize/Update WiZ devices

            # Set last update
            self.last_update = time.time()

            # Update devices
            conf.verb=0
            ans,unans=srp(Ether(dst="ff:ff:ff:ff:ff:ff")/ARP(pdst=Parameters["Mode2"]), timeout=2)

            hostNames = []

            for snd,rcv in ans:
                ipAddress=rcv.sprintf(r"%ARP.psrc%")
                try:
                    hostName = socket.gethostbyaddr(ipAddress)
                except:
                    hostName = "Onbekend"

                if hostName[0][0:3] in Parameters["Mode1"]:
                    hostNames.append(hostName[0])

            for hostName in hostNames:
                Domoticz.Debug("Endpoint '"+hostName+"' found.")
                deviceFound = False
                for Device in Devices:
                    if ((hostName == Devices[Device].DeviceID)): deviceFound = True

                    host = str(Devices[Device].DeviceID)
                    port = 38899

                    mJSON = b'{"method":"getPilot"}'
                    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
                    try:
                        sock.sendto(mJSON, (host, port))
        
                        received = sock.recv(1024)
                    finally:
                        sock.close()
        
                    received=json.loads(received)
                    wizstate=received["result"]["state"]
                    if wizstate:
                        wizstate = 1
                    else:
                        wizstate = 0
                    wizlevel=str(received["result"]["dimming"])

                    if Devices[Device].Color != "":
                        c=json.loads(Devices[Device].Color)
                        try:
                            wizcw=received["result"]["c"]
                            wizww=received["result"]["w"]

                            c=json.loads(Devices[Device].Color)
                            c["cw"] = wizcw
                            c["ww"] = wizww
                        except:
                            wiztemp=received["result"]["temp"] 
                            c["t"] = (wiztemp - 2700) / 14.9
                        
                        wizcolor=json.dumps(c)
                    else:
                       wizcolor=""
                        
                    # Update status of Domoticz device
                    Devices[Device].Update(nValue=wizstate, sValue=wizlevel, TimedOut=False, Color=wizcolor)

                if (deviceFound == False):
                    Domoticz.Device(Name=hostName, DeviceID=hostName,  Unit=len(Devices)+1, Type=241, Subtype=8, Switchtype=7, Image=0).Create()

        except Exception as err:
            Domoticz.Error("handleThread: "+str(err)+' line '+format(sys.exc_info()[-1].tb_lineno))


global _plugin
_plugin = BasePlugin()

def onStart():
    global _plugin
    _plugin.onStart()

def onStop():
    global _plugin
    _plugin.onStop()

def onConnect(Connection, Status, Description):
    global _plugin
    _plugin.onConnect(Connection, Status, Description)

def onMessage(Connection, Data):
    global _plugin
    _plugin.onMessage(Connection, Data)

def onCommand(Unit, Command, Level, Color):
    global _plugin
    _plugin.onCommand(Unit, Command, Level, Color)

def onNotification(Name, Subject, Text, Status, Priority, Sound, ImageFile):
    global _plugin
    _plugin.onNotification(Name, Subject, Text, Status, Priority, Sound, ImageFile)

def onDisconnect(Connection):
    global _plugin
    _plugin.onDisconnect(Connection)

def onHeartbeat():
    global _plugin
    _plugin.onHeartbeat()

    # Generic helper functions
def DumpConfigToLog():
    for x in Parameters:
        if Parameters[x] != "":
            Domoticz.Debug( "'" + x + "':'" + str(Parameters[x]) + "'")
    Domoticz.Debug("Device count: " + str(len(Devices)))
    for x in Devices:
        Domoticz.Debug("Device:           " + str(x) + " - " + str(Devices[x]))
        Domoticz.Debug("Device ID:       '" + str(Devices[x].ID) + "'")
        Domoticz.Debug("Device Name:     '" + Devices[x].Name + "'")
        Domoticz.Debug("Device nValue:    " + str(Devices[x].nValue))
        Domoticz.Debug("Device sValue:   '" + Devices[x].sValue + "'")
        Domoticz.Debug("Device LastLevel: " + str(Devices[x].LastLevel))
    return

# Loop thru domoticz devices and see if there's a device with matching DeviceID, if so, return unit number, otherwise return zero
def getUnit(devid):
    unit = 0
    for x in Devices:
        if Devices[x].DeviceID == devid:
            unit = x
            break
    return unit

# Find the smallest unit number available to add a device in domoticz
def nextUnit():
    unit = 1
    while unit in Devices and unit < 255:
        unit = unit + 1
    return unit

def UpdateDevice(Unit, nValue, sValue, TimedOut):
    # Make sure that the Domoticz device still exists (they can be deleted) before updating it
    if (Unit in Devices):
        #if (Devices[Unit].nValue != nValue) or (Devices[Unit].sValue != sValue) or (Devices[Unit].TimedOut != TimedOut):
        Devices[Unit].Update(nValue=nValue, sValue=str(sValue), TimedOut=TimedOut)
        Domoticz.Log("Update "+str(nValue)+":'"+str(sValue)+"' ("+Devices[Unit].Name+") TimedOut="+str(TimedOut))
    return
