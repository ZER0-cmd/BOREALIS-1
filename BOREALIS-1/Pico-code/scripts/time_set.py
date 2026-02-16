from machine import Pin, I2C
from drivers.rtc_ds3231 import DS3231

# ==== EDIT THESE TO CURRENT UTC ====
YEAR   = 2025
MONTH  = 12
DAY    = 6
HOUR   = 12  # 24h UTC
MINUTE = 12
SECOND = 0
# ===================================

# weekday doesn’t really matter much; set to 1 (Monday) if you don’t care
WEEKDAY = 6

i2c = I2C(0, sda=Pin(0), scl=Pin(1), freq=400000)
rtc_ext = DS3231(i2c)

rtc_ext.datetime((YEAR, MONTH, DAY, WEEKDAY, HOUR, MINUTE, SECOND, 0))

print("DS3231 set to:", rtc_ext.datetime())
