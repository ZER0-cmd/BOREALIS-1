from machine import ADC, Pin, I2C
import config

from drivers.sensor_sht31 import SHT31

from drivers.bmp390 import BMP390
from drivers.mpu6500 import MPU6500


SENSOR_NONE = "none"
SENSOR_HUMIDITY = "humidity"
SENSOR_PRESSURE = "pressure"
SENSOR_MPU6500 = "mpu6500"
SENSOR_LIGHT = "uv"
SENSOR_GAS = "gas"
SENSOR_SOLAR = "solar"
SENSOR_TEMP = "temperature"
SENSOR_UNKNOWN = "unknown"

SENSOR_MAP = [
    (config.SENSOR_NONE_ID, SENSOR_NONE),
    (config.SENSOR_HUMIDITY_ID, SENSOR_HUMIDITY),
    (config.SENSOR_PRESSURE_ID, SENSOR_PRESSURE),
    (config.SENSOR_MPU6500_ID, SENSOR_MPU6500),
    (config.SENSOR_GAS_ID, SENSOR_GAS),
    (config.SENSOR_LIGHT_ID, SENSOR_LIGHT),
    (config.SENSOR_SOLAR_ID, SENSOR_SOLAR),
    (config.SENSOR_TEMP_ID, SENSOR_TEMP)
]


class SensorManager:
    def __init__(self):
        self.adc = ADC(config.SENSOR_ID_ADC_PIN)

        self.i2c = I2C(
            config.SENSOR_I2C_ID,
            sda=Pin(config.SENSOR_I2C_SDA),
            scl=Pin(config.SENSOR_I2C_SCL),
            freq=config.SENSOR_I2C_FREQ,
        )

        self.current_kind = None
        self.sensor = None

    def read_adc(self):
        return self.adc.read_u16()

    def classify(self, adc_value):
        rangechk = lambda x, r : r[0] <= x < r[1]

        for id, kind in SENSOR_MAP:
            if rangechk(adc_value, id):
                return kind

        return SENSOR_UNKNOWN

    def connect_for_kind(self, kind):
        self.sensor = None
        self.current_kind = kind

        if kind == SENSOR_NONE:
            return

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

    def refresh_connection(self):
        adc_value = self.read_adc()
        kind = self.classify(adc_value)

        changed = (kind != self.current_kind)
        if changed:
            self.connect_for_kind(kind)

        return changed, kind, adc_value

    def read_data(self):
        if self.current_kind == SENSOR_NONE:
            return None

        if self.current_kind == SENSOR_UNKNOWN:
            return {
                "kind": SENSOR_UNKNOWN,
                "adc": self.read_adc(),
            }

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
                "temperature_c": temp_c,
                "pressure_hpa": pressure_pa / 100.0,
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

        return None