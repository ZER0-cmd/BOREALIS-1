import time
from machine import Pin, I2C
from drivers.bmp390 import BMP390

i2c = I2C(1, sda=Pin(14), scl=Pin(15), freq=100000)

print("I2C scan:", [hex(x) for x in i2c.scan()])

sensor = None

for addr in (0x77, 0x76):
    try:
        sensor = BMP390(i2c, address=addr)
        print("BMP3xx found at", hex(addr), "chip id =", hex(sensor.chip_id))
        break
    except Exception as e:
        print("No BMP3xx at", hex(addr), "-", e)

if sensor is None:
    raise RuntimeError("BMP3xx not found")

print("Starting BMP3xx test...")

while True:
    try:
        temp_c, pressure_pa = sensor.read()
        pressure_hpa = pressure_pa / 100.0

        print(
            "Temperature: {:.2f} C | Pressure: {:.2f} hPa".format(
                temp_c, pressure_hpa
            )
        )
    except Exception as e:
        print("Read failed:", e)

    time.sleep(2)