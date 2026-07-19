# Run: mpremote mount Pico-code exec "TIME_STR='$(date +"%Y %m %d %w %H %M %S")'" run scripts/time_set.py

from machine import Pin, I2C
from drivers.rtc_ds1302 import DS1302
import config

# "%Y %m %d %w %H %M %S"
TIME = [int(x) for x in TIME_STR.split(" ")]

rtc = DS1302(
                Pin(config.DS1302_CLK),
                Pin(config.DS1302_DAT),
                Pin(config.DS1302_CE),
            )

rtc.datetime(tuple(TIME + [0]))

print("DS3231 set to:", rtc.datetime())