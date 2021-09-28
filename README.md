WiZ connected Plugin for Domoticz home automation

Controls WiZ connected devices your network (mainly on/off switches and Lights). WiZ devices come in many brands like WiZ connected, Philips and TAO  and may come with different apps, so select the matching App when configuring the plugin.

## Key Features

* Auto-detects devices in your network
* Tested with WiZ whites lights (but should control other devices on/off)
* Allows controlling Dimmer/Cold-Warm for lights
* When device operated by app, Domoticz is synchronized every 10 seconds

## pre requirements

* Up and running DNS server (with recursive lookup enabled)

## Installation

Python version 3.4 or higher required & Domoticz version 2021.1 or greater.

To install:
* Go in your Domoticz directory using a command line and open the plugins directory.
* The plugin required Python library scapy ```sudo apt-get install python-scapy```
* Run: ```git clone https://github.com/sydspost/Domoticz-WiZ-connected-plugin.git```
* Restart Domoticz. ```sudo systemctl restart domoticz```

## Updating

To update:
* Go in your Domoticz directory using a command line and open the plugins directory then the Domoticz-wizconnected directory.
* Run: ```git pull```
* Restart Domoticz.

## Configuration
Hostname Prefix: The first 4-letters of the default prefix your WiZ connected brand gives to your hostname, in case of a WiZ connected device it's "wiz_". Didn't test this with devices from other brands. But you can specify multiple prefixes by deviding them with a comma, for instance "wiz-,phil"

Subnet: Enter your subnet in het format "255.255.255.0/24" (in case of Class C subnet)

## Usage

In the web UI, navigate to the Hardware page. In the hardware dropdown there will be an entry called "WiZ connected" -- configure and add the hardware there.
Devices detected are created in the 'Devices' tab, to use them you need to click the green arrow icon and 'Add' them to Domoticz.

## Change log

| Version | Information|
| ----- | ---------- |
| 1.0.0 | Initial upload version |

## Remarks
The plugin uses Arp ping to detect your WiZ connected devices on your local network, causing to enter your network card in promiscious mode when running. To prevent your syslog is running full with entering and leaving promiscious mode messages, put your network card permanent in promiscious mode with: sudo ifconfig eth0 promisc
