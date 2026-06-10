import drivers.scd4x
from machine import I2C, Pin
import config
import time

sensor = drivers.scd4x.SCD41(I2C(config.SENSOR_I2C_ID, scl=Pin(config.SENSOR_I2C_SCL), sda=Pin(config.SENSOR_I2C_SDA), freq=config.SENSOR_I2C_FREQ))
while True:
    sensor.trigger()
    while not sensor.ready():
        time.sleep(0.1)
    print(sensor.read()[0])