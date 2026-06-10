import time
from machine import Pin, I2C
from drivers.mpu6500 import MPU6500

# Pico I2C1
# SDA = GPIO14 -> pin 19
# SCL = GPIO15 -> pin 20
i2c = I2C(1, sda=Pin(14), scl=Pin(15), freq=100000)

print("I2C scan:", [hex(x) for x in i2c.scan()])

sensor = None

for addr in (0x68, 0x69):
    try:
        sensor = MPU6500(i2c, address=addr)
        print("MPU6500 found at", hex(addr))
        break
    except Exception as e:
        print("No MPU6500 at", hex(addr), "-", e)

if sensor is None:
    raise RuntimeError("MPU6500 not found")

print("Starting MPU6500 test...")

while True:
    try:
        ax, ay, az = sensor.read_accel()
        gx, gy, gz = sensor.read_gyro()
        temp = sensor.read_temperature()

        print(
            "Accel[g]: X={:.3f} Y={:.3f} Z={:.3f} | "
            "Gyro[dps]: X={:.2f} Y={:.2f} Z={:.2f} | "
            "Temp={:.2f} C".format(
                ax, ay, az, gx, gy, gz, temp
            )
        )
    except Exception as e:
        print("Read failed:", e)

    time.sleep(0.5)