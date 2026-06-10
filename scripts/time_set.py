# Run: mpremote run scripts/time_set.py (Get-Date -Format "yyyy MM dd w HH mm ss")


from machine import Pin, I2C
from drivers.rtc_ds3231 import DS3231
import sys

# "%Y %m %d %w %H %M %S"
TIME = sys.argv

i2c = I2C(0, sda=Pin(0), scl=Pin(1), freq=400000)
rtc_ext = DS3231(i2c)

rtc_ext.datetime((*TIME, 0))

print("DS3231 set to:", rtc_ext.datetime())