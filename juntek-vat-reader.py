# requires 'bitstring', 'pyserial'
import datetime

import serial
from enum import Enum
from bitstring import ConstBitStream

HDRA = b'\xAA'
HDRB = b'\x1C'

# You will need to change this to /dev/ACM... or /dev/tty... on linux/mac etc.
PORT = "COM12"


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