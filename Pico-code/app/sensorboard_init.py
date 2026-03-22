from machine import ADC
import drivers.ADS1115 as ADS1115 # ADC to I2C
import drivers.bmp390 as BMP390 # Pressure
import drivers.ltr390 as LTR390 # UV
from drivers.max31865 import MAX31865 as PT100 # Temperature
import drivers.scd4x as SCD41 # CO2
import drivers.MPU6050 as MPU6050 # Acceleration and gyroscope
import drivers.mpu9250 as MPU9250 # Magnetic field


class identify:
    def __init__(self, i2c, spi, cs, id, safe:SafeModeManager):
        voltage = ADC(id) # Replace with correct pin number.
        if voltage <= .05:
            safe.set_error(LEVEL_WARNING, "identify", Exception("No sensor detected:", voltage))
        resistance = float(voltage) # Insert voltage divider formula.
        rescheck = lambda target : target-2 < resistance < target+2

        if rescheck(10):
            sensor = ADS1115(i2c=i2c) # What is this supposed to do? Library: https://github.com/joy-it/ADS1115-Micropython/tree/main

        elif rescheck(15):
            try:
                sensor = BMP390.bmp390mod(BMP390.bus_service.I2cAdapter(i2c))
                sensor.soft_reset()
                calibration_data = [sensor.get_calibration_coefficient(index) for index in range(14)]
                sensor.set_oversampling(pressure_oversampling=2, temperature_oversampling=3)
                sensor.set_sampling_period(5)
                sensor.set_iir_filter(2)
            except Exception as e:
                safe.set_error(LEVEL_DEGRADED, 'BMP390_init', e)
            def _read():
                status = sensor.get_data_status()
                sensor.start_measurement(enable_press=True, enable_temp=False, mode=1)
                if status.cmd_decoder_ready and status.press_ready:
                    return sensor.get_pressure()
                return 'NaN'

        elif rescheck(20):
            try:
                sensor = LTR390(i2c=i2c)
            except Exception as e:
                safe.set_error(LEVEL_DEGRADED, 'LTR390_init', e)
            def _read():
                try:
                    return sensor.uvs()
                except Exception:
                    return 'NaN'
            
        elif rescheck(25):
            try:
                sensor = PT100(spi=spi, cs=cs)
            except Exception as e:
                safe.set_error(LEVEL_DEGRADED, 'PT100_init', e)
            def _read():
                try:
                    return sensor.temperature
                except Exception:
                    return 'NaN'

        elif rescheck(30):
            try:
                sensor = SCD41(i2c_bus=i2c)
                sensor.start_periodic_measurement()
            except Exception as e:
                safe.set_error(LEVEL_DEGRADED, 'SCD41_init', e)
            def _read():
                try:
                    return sensor.co2
                except Exception:
                    return 'NaN'

        else:
            safe.set_error(LEVEL_WARNING, "identify", Exception("Unknown sensor resistance:", resistance))
            self.sensor = None
            def _read():
                return None
            self.name = None
        
        self.read = _read
        self.sensor = sensor
        self.resistance = resistance
