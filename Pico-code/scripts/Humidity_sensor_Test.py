from machine import Pin, I2C
import time
from sensor_sht31 import SHT31

# I2C1 on Raspberry Pi Pico
# SDA = GPIO14 (physical pin 19)
# SCL = GPIO15 (physical pin 20)
i2c = I2C(1, scl=Pin(15), sda=Pin(14), freq=100000)

# Create sensor object
sensor = SHT31(i2c)

print("Starting SHT31 read test...")

while True:
    try:
        temperature, humidity = sensor.read()
        print("Temperature: {:.2f} C | Humidity: {:.2f} %RH".format(temperature, humidity))
    except Exception as e:
        print("Sensor read failed:", e)

    time.sleep(2)