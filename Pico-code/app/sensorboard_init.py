from machine import I2C, SPI, Pin, ADC
import drivers.ADS1115 as ADS1115 # ADC to I2C
import drivers.bmp390 as BMP390 # Pressure
import drivers.ltr390 as LTR390 # UV
from drivers.MAX31865_simple import MAX31865 as PT100 # Temperature
import drivers.scd4x as SCD41 # CO2
import drivers.MPU6050 as MPU6050 # Acceleration and gyroscope
import drivers.mpu9250 as MPU9250 # Magnetic field

from app.safe_mode import (
    SafeModeManager,
    LEVEL_OK, LEVEL_WARNING, LEVEL_DEGRADED, LEVEL_CRITICAL, LEVEL_FATAL,
    level_name,
)
safe = SafeModeManager() # Insert config

i2c = I2C(id=1, scl=Pin(7), sda=Pin(6), freq=400_000)
spi = SPI(0, baudrate=400_000, polarity=0, phase=1)
cs = Pin(29)

def identify(resistance):
    voltage = ADC(Pin(7, Pin.IN)) # Replace with correct pin number.
    if voltage <= 1.:
        safe.set_error(LEVEL_WARNING, "identify", Exception("No sensor detected:", voltage))
    resistance = float(voltage) # Insert voltage divider formula.
    match resistance: # Replace with correct resistance values for each sensor.
        case 5.:
            sensor = ADS1115(i2c=i2c)
        case 10.:
            sensor = BMP390.bmp390mod(BMP390.bus_service.I2cAdapter(i2c))
        case 15.:
            sensor = LTR390(i2c=i2c)
        case 20.:
            sensor = PT100(spi=spi, cs=cs)
        case 25.:
            sensor = SCD41(i2c_bus=i2c)
        case 30.:
            sensor = MPU6050(i2c=i2c)
        case 35.:
            sensor = MPU9250(i2c=i2c)
        case _:
            safe.set_error(LEVEL_WARNING, "identify", Exception("Unknown sensor resistance:", resistance))
            return None
    return sensor

sensor = identify()
try:
    sensor.init()
except Exception as e:
    safe.set_error(LEVEL_CRITICAL, "sensor_init", e)
