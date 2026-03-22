from machine import I2C, Pin
import time
from drivers.mmc5603 import MMC5603
import config


i2c = I2C(config.SENSOR_I2C_ID, scl=Pin(config.SENSOR_I2C_SCL), sda=Pin(config.SENSOR_I2C_SDA), freq=config.SENSOR_I2C_FREQ)

print("Scanning I2C bus...")
print([hex(addr) for addr in i2c.scan()])

try:
    # Initialize the sensor
    sensor = MMC5603(i2c)
    print("MMC5603NJ successfully initialized!")
    xa = 0
    ya = 0
    za = 0
    for i in range(1000):
        x, y, z = sensor.read_raw()
        xa += x/1000
        ya += y/1000
        za += z/1000
        time.sleep(0.1)
        
    print('calibration done')

    while True:
        # Read the magnetic field
        x, y, z = sensor.read_raw()
        x -= int(xa)
        y -= int(ya)
        z -= int(za)
        
        # Print the results
        print(f"X: {x:8d} | Y: {y:8d} | Z: {z:8d}")
        
        time.sleep(0.1)

except Exception as e:
    print(f"Error: {e}")