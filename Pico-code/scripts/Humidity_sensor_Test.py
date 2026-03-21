import time
from machine import Pin, I2C

from drivers.sensor_sht31 import SHT31  

# I2C setup (Pico)
i2c = I2C(
    1,
    scl=Pin(15),   # GPIO15 → pin 20
    sda=Pin(14),   # GPIO14 → pin 19
    freq=100000
)

# Create sensor
sensor = SHT31(i2c)

print("Starting SHT31 read test...")

while True:
    try:
        temperature, humidity = sensor.read()
        print("Temperature: {:.2f} C | Humidity: {:.2f} %RH".format(temperature, humidity))
    except Exception as e:
        print("Sensor read failed:", e)

    time.sleep(2)