# requires 'bitstring', 'pyserial'
import datetime

import serial
from enum import Enum
from bitstring import ConstBitStream
import paho.mqtt.client as mqtt


HDRA = b'\xAA'
HDRB = b'\x1C'

# You will need to change this to /dev/ACM... or /dev/tty... on linux/mac etc.
PORT = "COM12"
#Optional mqtt setup

# Def for mqqt connection
def on_connect(client, userdata, flags, rc):
	print("Connected to MQTT server with result code :"+str(rc))

#Mqtt details 
#Username for mqtt
user = ""
#Password for mqtt
password = ""
#Unique mqtt client name
client = mqtt.Client("")
client.username_pw_set(user, password)    #set username and password
client.on_connect = on_connect
#Provide IP Address for you mqtt server and port
client.connect("ip_address", 1883, 60) # use your MQTT server name
client.loop_start()

#Mqtt topic to publish the data to below is an example

topic_volts="topic/volts"
topic_amps="topic/amps"
topic_watts="topic/watts"
topic_amp_hour="topic/amp_hour"
topic_watt_hour="topic/watt_hour"
topic_uptime="topic/uptime"
topic_temperature="topic/temperature"

class State(Enum):
    START = 0
    READY = 1


class Packet:
    def __init__(self, pkt):
        bs = ConstBitStream(pkt)
        print('data:', pkt.hex())
        self.frequency = bs.read('uint:8')
        self.address = bs.read('uint:8')
        self.volts = float(bs.read('uint:16')) / 100.0
        self.amps = float(bs.read('int:16')) / 10.0
        self.watts = float(bs.read('uint:32')) / 1000.0
        self.amp_hour = float(bs.read('uint:32')) / 1000.0
        self.watt_hour = float(bs.read('uint:32')) / 1000.0
        self.uptime = bs.read('uint:32')
        self.status = bs.read('uint:8')
        self.temperature = bs.read('int:8')
        self.unknown_w = bs.read('uint:16')
        self.unknown_x = bs.read('uint:16')
        self.unknown_y = bs.read('uint:16')
        self.unknown_z = bs.read('uint:16')
        #  TODO; update this.
        #  w     |  x      | y     | z
        #  00 00 |  06  aa | 04 01 | 20 cf
        #               0  | 1  2  | 3  4
        #  zeros | crc? (display poll cmd)

    def print2(self):
        print('--------------------------------------------------------')
        print('Frequency.:', self.frequency, 'Address..:', self.address)
        print('Volts......:', self.volts, 'Amps.....:', self.amps)
        print('Ah.........:', self.amp_hour, 'Wh.......:', self.watt_hour)
        print('Uptime.....:', datetime.timedelta(0, self.uptime), 'Status...:', self.status)
        print('Temperature:', self.temperature)
        print('Unknown   W:', self.unknown_w)
        print('Unknown   X:', self.unknown_x)
        print('Unknown   Y:', self.unknown_y)
        print('Unknown   Z:', self.unknown_z)

    def print(self):
        print('Frequency:', self.frequency, 'Address..:', self.address,
              'Volts:', self.volts, 'Amps:', self.amps,
              'Ah:', self.amp_hour, 'Wh:', self.watt_hour,
              'Uptime:', datetime.timedelta(0, self.uptime), 'Status:', self.status,
              'Temperature:', self.temperature,
              'W:', self.unknown_w, 'X:', self.unknown_x,
              'Y:', self.unknown_y, 'Z:', self.unknown_z)
        print("Sending MQTT message...")
	client.publish(topic_volts,self.volts,0,False)
	client.publish(topic_amps,self.amps,0,False)
	client.publish(topic_watts,self.watts,0,False)
	client.publish(topic_amp_hour,self.amp_hour,0,False)
	client.publish(topic_watt_hour,self.watt_hour,0,False)
	client.publish(topic_uptime,self.uptime,0,False)
	client.publish(topic_status,self.status,0,False)
	client.publish(topic_temperature,self.temperature,0,False)


with serial.Serial(PORT,
                   baudrate=57600,
                   bytesize=serial.EIGHTBITS,
                   parity=serial.PARITY_NONE,
                   stopbits=serial.STOPBITS_ONE
                   ) as ser:
    state = State.START
    while True:
        print('reading one byte...')
        data = ser.read()
        print("Recv'd:", data.hex(), "state:", state)
        if state == State.START and data == HDRA:
            state = State.READY
            continue
        if state == State.READY and data == HDRB:
            state = State.START
            data = ser.read(32)
            packet = Packet(data)
            packet.print()

# commands my display sends to get data out of the shunt (I have a VAT 1030)
#    out_a = b'\xAA\x04\x00\x20\xCE'
#    out_b = b'\xAA\x04\x20\x20\xD0'
#    out_c = b'\xAA\x04\x01\x20\xCF'

# most of the heavy lifting done by these guys
# https://www.youtube.com/watch?v=IRnvLcwpoJU
# https://github.com/rjflatley/vat1300
# https://secondlifestorage.com/index.php?threads/rs485-rs232-modbus-everything.10500/
# http://evbitz.uk/Other_Stuff..._files/Juntek%20-%204300%20Wireless%20Meter%20-%20User%20Guide.pdf
