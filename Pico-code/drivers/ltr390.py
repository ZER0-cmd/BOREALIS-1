# DFRobot SEN0540 LTR390 UV Sensor library
# by Toby Corkindale https://github.com/TJC/
# Released under the Apache 2.0 license.
#
# This library is for the DFRobot LTR390 UV Sensor.
# It is NOT compatible with regular LTR390 chips -- I don't know why it is
# different.
# Most notably, when writing to a register, it has to be sent with a +5 offset
# to the address. The data written must be two bytes, with the second byte
# being zero.

from micropython import const

DEV_ADDRESS = const(0x1C)

# Input Register
REG_PID = const(0x00)  # Device PID
REG_VID = const(0x01)  # Device VID, fixed to 0x3343
REG_ADDR = const(0x02)  # Device address of module
REG_BAUDRATE = const(0x03)  # Serial baud rate
REG_STOPBIT = const(0x04)  # Serial check bit and stop bit
REG_VERSION = const(0x05)  # Firmware version
REG_PART_ID = const(0x06)  # Device ID of sensor
REG_ALS_DATA_LOW = const(0x07)  # The low bit of ambient light intensity
REG_ALS_DATA_HIGH = const(0x08)  # The high bit of ambient light intensity
REG_UVS_DATA_LOW = const(0x09)  # The low bit of UV intensity
REG_UVS_DATA_HIGH = const(0x0A)  # The high bit of UV intensity

REG_MAIN_CTRL = const(0x0E)  # Sensor mode select
REG_MEASURE_RATE = const(0x0D)  # Resolution and sampling time setting
REG_GAIN = const(0x06)  # Gain adjustment

REG_INT_CFG = const(0x07)  # Interrupt config

# The lower bit of upper threshold of UV or ambient light
REG_THRESH_UP_DATA_LOW = const(0x08)
REG_THRESH_UP_DATA_HIGH = const(0x09)

# The low bit of lower threshold of UV or ambient light
REG_THRESH_LOW_DATA_LOW = const(0x0A)
REG_THRESH_LOW_DATA_HIGH = const(0x0B)

# Threshold of UV or ambient light data change counts
REG_THRESH_VAR_DATA = const(0x0C)

eGain1 = const(0)  # Gain of 1
eGain3 = const(1)  # Gain of 3
eGain6 = const(2)  # Gain of 6
eGain9 = const(3)  # Gain of 9
eGain18 = const(4)  # Gain of 18

# Note when selecting resolution and time frames -- the higher the
# resolution, the longer the minimum latency.
e20bit = const(0)  # 20-bit data, min time 400ms
e19bit = const(16)  # 19-bit data, min time 200ms
e18bit = const(32)  # 18-bit data, min time 100ms
e17bit = const(48)  # 17-bit data, min time 50ms
e16bit = const(64)  # 16-bit data, min time 25ms

e25ms = const(0)  # Sampling time of 25ms
e50ms = const(1)  # Sampling time of 50ms
e100ms = const(2)  # Sampling time of 100ms
e200ms = const(3)  # Sampling time of 200ms
e500ms = const(4)  # Sampling time of 500ms
e1000ms = const(5)  # Sampling time of 1000ms
e2000ms = const(6)  # Sampling time of 2000ms


class LTR390:
    # Pass in an initialised I2C object, eg
    # i2c = I2C(0, scl=Pin(39), sda=Pin(40), freq=100_000)
    # ltr = LTR390(i2c)
    # ltr.set_uvs()
    # print(ltr.uvs())
    # If you have issues, try sleeping for 100ms first to let the system stabilise
    def __init__(self, i2c):
        self.i2c = i2c
        self.set_uvs()
        self.set_measure_rate(e18bit, e200ms)
        self.set_gain(eGain6)

    def set_als(self):
        self.i2c.writeto_mem(DEV_ADDRESS, REG_MAIN_CTRL + 5, bytes([0x02, 0]))

    def set_uvs(self):
        self.i2c.writeto_mem(DEV_ADDRESS, REG_MAIN_CTRL + 5, bytes([0x0A, 0]))

    def set_measure_rate(self, bitrate, latency):
        self.i2c.writeto_mem(
            DEV_ADDRESS,
            REG_MEASURE_RATE + 5,
            bytes([bitrate + latency, 0]),
        )

    def set_gain(self, gainLevel):
        self.i2c.writeto_mem(DEV_ADDRESS, REG_GAIN + 5, bytes([gainLevel, 0]))

    def uvs(self):
        buffer = self.i2c.readfrom_mem(DEV_ADDRESS, REG_UVS_DATA_LOW, 4)
        return (buffer[3] << 24) + (buffer[2] << 16) + (buffer[1] << 8) + buffer[0]

    def als(self):
        buffer = self.i2c.readfrom_mem(DEV_ADDRESS, REG_ALS_DATA_LOW, 4)
        return (buffer[3] << 24) + (buffer[2] << 16) + (buffer[1] << 8) + buffer[0]
