from machine import I2C, Pin
import time

from drivers.scd4x import SCD4X

# Same bus style as your other sensor tests
i2c = I2C(1, sda=Pin(14), scl=Pin(15), freq=100000)

print("I2C scan:", [hex(x) for x in i2c.scan()])

sensor = SCD4X(i2c, address=0x62)

print("Starting periodic measurement...")
sensor.start_periodic_measurement()

print("Waiting for valid measurements...")

start_time = time.ticks_ms()

while True:
    try:
        if sensor.data_ready:
            co2 = sensor.co2
            temp_c = sensor.temperature
            rh = sensor.relative_humidity

            print(
                "CO2: {} ppm | Temperature: {:.2f} C | Humidity: {:.2f} %RH".format(
                    co2, temp_c, rh
                )
            )
        else:
            print("Data not ready yet...")

    except Exception as e:
        print("Read failed:", e)

    time.sleep(1)