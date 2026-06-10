from machine import I2C, Pin
import time
from drivers.mmc5603 import MMC5603
import config


i2c = I2C(config.SENSOR_I2C_ID, scl=Pin(config.SENSOR_I2C_SCL), sda=Pin(config.SENSOR_I2C_SDA), freq=config.SENSOR_I2C_FREQ)

print("Scanning I2C bus...")
print([hex(addr) for addr in i2c.scan()])

def calibrate_sensor(duration=20):
    print("Rotate slowly. Filtering noise...")
    mag_min = [1e6, 1e6, 1e6]
    mag_max = [-1e6, -1e6, -1e6]
    
    start_time = time.time()
    while time.time() - start_time < duration:
        # 1. Take several readings and average them to kill noise
        tx, ty, tz = 0, 0, 0
        samples = 10
        for _ in range(samples):
            rx, ry, rz = sensor.read_raw()
            tx += rx; ty += ry; tz += rz
        
        avg_raw = [tx/samples, ty/samples, tz/samples]

        # 2. Update Min/Max
        for i in range(3):
            if avg_raw[i] < mag_min[i]: mag_min[i] = avg_raw[i]
            if avg_raw[i] > mag_max[i]: mag_max[i] = avg_raw[i]
            
        time.sleep_ms(20)

    # Calculate Hard Iron
    offs = [(mag_max[i] + mag_min[i]) / 2 for i in range(3)]
    
    # Calculate Soft Iron (with a safety check)
    deltas = [(mag_max[i] - mag_min[i]) / 2 for i in range(3)]
    avg_delta = sum(deltas) / 3
    
    # Avoid division by zero and extreme scaling
    scales = []
    for d in deltas:
        if d > 0:
            s = avg_delta / d
            # Limit scale to reasonable bounds (0.5 to 2.0)
            scales.append(max(min(s, 2.0), 0.5))
        else:
            scales.append(1.0)
            
    return offs, scales

try:
    # Initialize the sensor
    sensor = MMC5603(i2c)
    sensor.set_resolution(0)
    print("MMC5603NJ successfully initialized!")

    (ox, oy, oz), (sx, sy, sz) = calibrate_sensor(30)

    while True:
        # Read the magnetic field
        x, y, z = sensor.read_raw()
        x = (x-ox)*sx
        y = (y-oy)*sy
        z = (z-oz)*sz
        
        # Print the results
        print(f"{x},{y},{z}")
        
        time.sleep(0.1)

except Exception as e:
    print(f"Error: {e}")