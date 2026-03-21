import time
from machine import Pin, I2C

import config
from drivers.display_ssd1306 import SSD1306_I2C
from drivers.output_led import LED
from drivers.sd_detect import SdDetect
from app.ui import Ui


class App:
    def __init__(self):
        # One status LED only
        self.status_led = LED(
            config.STATUS_LED_PIN,
            active_high=config.LED_ACTIVE_HIGH
        )

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

    def _run_startup_checks(self):
        """
        Run startup checks while the splash screen is visible.

        Current check:
        - microSD detect

        Returns:
            True if all checks pass
            False otherwise
        """
        start_ms = time.ticks_ms()
        splash_ms = config.OLED_SPLASH_MS

        led_state = False
        last_toggle_ms = start_ms
        blink_interval_ms = 100  # fast blink during startup check

        sd_ok = False

        while time.ticks_diff(time.ticks_ms(), start_ms) < splash_ms:
            now = time.ticks_ms()

            # Current system check
            sd_ok = self.sd_detect.is_inserted()

            # Fast LED blink during checking
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
        """
        Final LED behavior after startup check:
        - if OK: one success flash, then stay ON
        - if FAIL: stay OFF
        """
        if ok:
            # stop blink cleanly
            self.status_led.off()
            time.sleep_ms(80)

            # success flash
            self.status_led.on()
            time.sleep_ms(200)
            self.status_led.off()
            time.sleep_ms(120)

            # steady ON
            self.status_led.on()
        else:
            self.status_led.off()

    def run(self):
        # Show splash screen first
        self.ui.show_boot("pictures/logo.csv")

        # Run checks during splash screen time
        system_ok = self._run_startup_checks()

        # Show final LED result
        self._show_check_result(system_ok)

        # Go to idle screen
        self.ui.show_idle()

        while True:
            time.sleep_ms(200)