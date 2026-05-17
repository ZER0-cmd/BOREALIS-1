from machine import ADC, Pin, I2C
import time
import config
import gc

from drivers.sensor_sht31 import SHT31

from drivers.bmp390 import BMP390
from drivers.mpu6500 import MPU6500
from drivers.ADS1115 import ADS1115
from drivers.mmc5603 import MMC5603
from drivers import ltr390


SENSOR_NONE = config.SENSOR_NONE_ID
SENSOR_CO2 = config.SENSOR_CO2_ID
SENSOR_HUMIDITY = config.SENSOR_HUMIDITY_ID
SENSOR_PRESSURE = config.SENSOR_PRESSURE_ID
SENSOR_MPU6500 = config.SENSOR_MPU6500_ID
SENSOR_LIGHT = config.SENSOR_LIGHT_ID 
SENSOR_GAS = config.SENSOR_GAS_ID
SENSOR_SOLAR = config.SENSOR_SOLAR_ID
SENSOR_TEMP = config.SENSOR_TEMP_ID
SENSOR_MAGNET = config.SENSOR_MAGNETOMETER_ID
SENSOR_UNKNOWN = "unknown"

SENSOR_NAMES = {
    SENSOR_NONE : "No sensor",
    SENSOR_HUMIDITY : 'Humidity sensor',
    SENSOR_PRESSURE : 'Barometer',
    SENSOR_MPU6500 : 'Accelerometer',
    SENSOR_LIGHT : 'Light sensor',
    SENSOR_GAS : 'Gas sensor',
    SENSOR_SOLAR : 'Solar panel',
    SENSOR_TEMP : 'Termometer',
    SENSOR_CO2 : 'CO2 sensor',
    SENSOR_MAGNET : 'Magnetometer',
    SENSOR_UNKNOWN : "Unknown sensor"
}

class SensorManager:
    def __init__(self, i2c_adc=None):
        self.adc = ADC(config.SENSOR_ID_ADC_PIN)

        self.i2c = I2C(
            config.SENSOR_I2C_ID,
            sda=Pin(config.SENSOR_I2C_SDA),
            scl=Pin(config.SENSOR_I2C_SCL),
            freq=config.SENSOR_I2C_FREQ,
        )

        if i2c_adc is not None:
            self.i2c_adc = i2c_adc
        else:
            self.i2c_adc = I2C(
                config.ADC_I2C_ID,
                sda=Pin(config.ADC_I2C_SDA),
                scl=Pin(config.ADC_I2C_SCL),
                freq=config.ADC_I2C_FREQ,
            )

        self.current_kind = None
        self.sensor = None
        self._pending = None
        self._pcount = 0

    def read_adc(self): # ID
        return self.adc.read_u16()
    
    def _adc(self): # Actual ADC
        return self.sensor.read_voltage(config.ADC_CHANNEL)
    
    @staticmethod
    def classify(adc_value):
        closest = min([SENSOR_NONE, SENSOR_GAS, SENSOR_HUMIDITY, SENSOR_LIGHT, SENSOR_MPU6500, SENSOR_PRESSURE, SENSOR_SOLAR, SENSOR_TEMP, SENSOR_CO2, SENSOR_MAGNET], key=lambda x : abs(x-adc_value))
        if abs(adc_value - closest) > 3000:
            return SENSOR_UNKNOWN
        return closest

    def connect_for_kind(self, kind):
        self.sensor = None
        self.current_kind = kind
        gc.collect()

        time.sleep_ms(20)
        if kind == SENSOR_NONE:
            return
        try:
            if kind == SENSOR_HUMIDITY:
                self.sensor = SHT31(self.i2c)
                return

            if kind == SENSOR_PRESSURE:
                last_exc = None
                for addr in (0x77, 0x76):
                    try:
                        self.sensor = BMP390(self.i2c, address=addr)
                        return
                    except Exception as e:
                        last_exc = e
                if last_exc:
                    raise last_exc
                raise RuntimeError("BMP390 not found")

            if kind == SENSOR_MPU6500:
                last_exc = None
                for addr in (0x68, 0x69):
                    try:
                        self.sensor = MPU6500(self.i2c, address=addr)
                        return
                    except Exception as e:
                        last_exc = e
                if last_exc:
                    raise last_exc
                raise RuntimeError("MPU6500 not found")
            
            if kind == SENSOR_LIGHT:
                # note: als mode exclusive with uv
                self.sensor = ltr390.LTR390(self.i2c)
                self.gain = 1
                self.sensor.set_gain(ltr390.GAINS[self.gain])
                self.sensor.set_resolution(config.UV_RESOLUTION)
                self.sensor.enable_uv()
                time.sleep_ms(self.sensor._int_ms + 10)
                return
            
            if kind == SENSOR_MAGNET:
                self.sensor = MMC5603(self.i2c)
                self.sensor.set_resolution(0)
                self.qcal = self.sensor.read_raw()
                return
            
            if kind in (SENSOR_TEMP, SENSOR_SOLAR, SENSOR_GAS):
                self.sensor = ADS1115(self.i2c_adc)
        except Exception as e:
            self.current_kind = SENSOR_UNKNOWN
            self.sensor = None

    def refresh_connection(self):
        try:
            adc_value = self.read_adc()
            kind = self.classify(adc_value)
            
            if kind == self._pending:
                self._pcount += 1
            else:
                self._pending = kind
                self._pcount = 1

            if self._pcount >= 8 and kind != self.current_kind:
                self.connect_for_kind(kind)
                return True, kind, adc_value

            return False, kind, adc_value
        except Exception:
            return False, self.current_kind, 0

    def read_data(self):
        if self.current_kind == SENSOR_NONE:
            return None
        
        if self.current_kind == SENSOR_UNKNOWN:
            return {
                "kind": SENSOR_UNKNOWN,
                "adc": self.read_adc(),
            }

        try:
            if self.current_kind == SENSOR_HUMIDITY:
                temp_c, humidity = self.sensor.read()
                return {
                    "kind": SENSOR_HUMIDITY,
                    "temperature_c": temp_c,
                    "humidity_percent": humidity,
                }

            if self.current_kind == SENSOR_PRESSURE:
                temp_c, pressure_pa = self.sensor.read()
                return {
                    "kind": SENSOR_PRESSURE,
                    "pressure_hpa": pressure_pa / 100.0,
                    "temperature_c" : temp_c
                }

            if self.current_kind == SENSOR_MPU6500:
                ax, ay, az = self.sensor.read_accel()
                gx, gy, gz = self.sensor.read_gyro()
                temp_c = self.sensor.read_temperature()

                return {
                    "kind": SENSOR_MPU6500,
                    "temperature_c": temp_c,
                    "ax_g": ax,
                    "ay_g": ay,
                    "az_g": az,
                    "gx_dps": gx,
                    "gy_dps": gy,
                    "gz_dps": gz,
                }
            
            if self.current_kind == SENSOR_TEMP:
                v = self._adc()
                temp = (v - 1.25) / 0.005
                return {
                    "kind" : SENSOR_TEMP,
                    "temperature_c" : temp
                    }

            if self.current_kind == SENSOR_GAS:
                v = self._adc()
                return {'kind': SENSOR_GAS,
                        'alcohol': 1.5*v}
                

            if self.current_kind == SENSOR_LIGHT:
                # Can read ambient light too using .read_als() but was to tired to do.
                # uv = self.sensor.read_uv()
                # vmax = 2**config.UV_RESOLUTION
                # if uv > .7*vmax and self.gain > 0:
                #     while uv > .7*vmax and self.gain > 1:
                #         self.gain -= 1
                #         self.sensor.set_gain(ltr390.GAINS[self.gain])
                #         time.sleep_ms(self.sensor._int_ms + 10)
                #         uv = self.sensor.read_uv()
                # else:
                #     while uv < .1*vmax and self.gain < 4:
                #         self.gain += 1
                #         self.sensor.set_gain(ltr390.GAINS[self.gain])
                #         time.sleep_ms(self.sensor._int_ms + 10)
                #         uv = self.sensor.read_uv()
                # time.sleep_ms(self.sensor._int_ms + 10)
                # return {
                #     'kind' : SENSOR_LIGHT,
                #     'uvindex': self.sensor.uv_index(uv)
                return {
                    'kind' : SENSOR_LIGHT,
                    'uvindex': self.sensor.uv_index()
                }
            
            if self.current_kind == SENSOR_SOLAR:
                v = self._adc()
                return {
                    "kind" : SENSOR_SOLAR,
                    "voltage" : v
                    }
            if self.current_kind == SENSOR_MAGNET:
                x,y,z = self.sensor.read_raw()
                qx,qy,qz = self.qcal
                return {
                    'kind': SENSOR_MAGNET,
                    'rx': x,
                    'B_x': x - qx,
                    'ry': y,
                    'B_y': y - qy,
                    'rz': z,
                    'B_z': z - qz
                }
        except Exception:
            pass
        return None