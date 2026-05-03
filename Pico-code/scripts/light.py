import time
from machine import I2C, Pin
import config
from drivers import ltr390

i2c = I2C(
            config.SENSOR_I2C_ID,
            sda=Pin(config.SENSOR_I2C_SDA),
            scl=Pin(config.SENSOR_I2C_SCL),
            freq=config.SENSOR_I2C_FREQ,
        )

sensor = ltr390.LTR390(i2c)
gain = 1
sensor.set_gain(ltr390.GAINS[gain])
sensor.set_resolution(config.UV_RESOLUTION)
sensor.enable_uv()
time.sleep_ms(sensor._int_ms + 10)

while True:
    uv = sensor.uv_index()
    print(uv)
    time.sleep_ms(sensor._int_ms + 10)