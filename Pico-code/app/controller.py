import time
from machine import Pin, I2C

import config
from drivers.display_ssd1306 import SSD1306_I2C
from drivers.output_led import LED
from drivers.sd_detect import SdDetect
from app.ui import Ui
from app.sensor_manager import (
    SensorManager,
    SENSOR_NONE,
    SENSOR_HUMIDITY,
    SENSOR_PRESSURE,
    SENSOR_UNKNOWN,
)


class App:
    def __init__(self):
        self.status_led = LED(
            config.STATUS_LED_PIN,
            active_high=config.LED_ACTIVE_HIGH
        )

        # OLED / RTC bus
        self.i2c = I2C(
            config.I2C_ID,
            sda=Pin(config.I2C_SDA),
            scl=Pin(config.I2C_SCL),
            freq=config.I2C_FREQ,
        )

        addrs = self.i2c.scan()
        if config.OLED_I2C_ADDR not in addrs:
            raise OSError(
                "OLED not found at address 0x%02X. Found: %s"
                % (config.OLED_I2C_ADDR, [hex(a) for a in addrs])
            )

        self.oled = SSD1306_I2C(
            config.OLED_WIDTH,
            config.OLED_HEIGHT,
            self.i2c,
            addr=config.OLED_I2C_ADDR,
        )

        self.ui = Ui(self.oled)

        self.sd_detect = SdDetect(
            config.SD_DETECT_PIN,
            active_low=config.SD_DETECT_ACTIVE_LOW
        )

        self.sensor_manager = SensorManager()
        self.last_sensor_read_ms = 0

    def _run_startup_checks(self):
        """
        Run startup checks during the splash screen.
        Current check: microSD detect only.
        """
        start_ms = time.ticks_ms()
        splash_ms = config.OLED_SPLASH_MS

        led_state = False
        last_toggle_ms = start_ms
        blink_interval_ms = 100

        sd_ok = False

        while time.ticks_diff(time.ticks_ms(), start_ms) < splash_ms:
            now = time.ticks_ms()

            sd_ok = self.sd_detect.is_inserted()

            if time.ticks_diff(now, last_toggle_ms) >= blink_interval_ms:
                last_toggle_ms = now
                led_state = not led_state
                if led_state:
                    self.status_led.on()
                else:
                    self.status_led.off()

            time.sleep_ms(10)

        return sd_ok

    def _show_check_result(self, ok):
        if ok:
            self.status_led.off()
            time.sleep_ms(80)

            self.status_led.on()
            time.sleep_ms(200)
            self.status_led.off()
            time.sleep_ms(120)

            self.status_led.on()
        else:
            self.status_led.off()

    def _sensor_name(self, kind):
        if kind == SENSOR_HUMIDITY:
            return "Humidity sensor"
        if kind == SENSOR_PRESSURE:
            return "Pressure sensor"
        if kind == SENSOR_UNKNOWN:
            return "Unknown sensor"
        return "No sensor"

    def run(self):
        # 1. Boot splash stays exactly first
        self.ui.show_boot("pictures/logo.csv")

        # 2. System checks happen during splash
        system_ok = self._run_startup_checks()

        # 3. Final LED state after startup checks
        self._show_check_result(system_ok)

        # 4. Only now start sensor logic
        self.ui.show_sensor_disconnected()

        while True:
            try:
                changed, kind, adc_value = self.sensor_manager.refresh_connection()

                if changed:
                    if kind == SENSOR_NONE:
                        self.ui.show_sensor_disconnected()
                        time.sleep_ms(config.SENSOR_ANNOUNCE_MS)
                    elif kind == SENSOR_UNKNOWN:
                        self.ui.show_unknown_sensor(adc_value)
                        time.sleep_ms(config.SENSOR_ANNOUNCE_MS)
                    else:
                        self.ui.show_sensor_connected(self._sensor_name(kind))
                        time.sleep_ms(config.SENSOR_ANNOUNCE_MS)

                now = time.ticks_ms()
                if time.ticks_diff(now, self.last_sensor_read_ms) >= config.SENSOR_READ_INTERVAL_MS:
                    self.last_sensor_read_ms = now

                    data = self.sensor_manager.read_data()

                    if data is None:
                        self.ui.show_sensor_disconnected()
                    elif data["kind"] == SENSOR_UNKNOWN:
                        self.ui.show_unknown_sensor(data["adc"])
                    elif data["kind"] == SENSOR_HUMIDITY:
                        self.ui.show_humidity_data(
                            data["temperature_c"],
                            data["humidity_percent"]
                        )
                    elif data["kind"] == SENSOR_PRESSURE:
                        self.ui.show_pressure_data(
                            data["temperature_c"],
                            data["pressure_hpa"]
                        )

            except Exception as e:
                self.ui.show_error(str(e))

            time.sleep_ms(100)