import time
from machine import Pin, I2C, SPI

import config

from drivers.display_ssd1306 import SSD1306_I2C
from drivers.sensor_sht31 import SHT31
from drivers.rtc_ds3231 import DS3231
from drivers.storage_sdcard import SDCard
from drivers.input_button import Button
from drivers.output_led import LED

from app.timekeeping import Timekeeper
from app.logging import SdLogger
from app.ui import Ui

from app.safe_mode import (
    SafeModeManager,
    LEVEL_OK, LEVEL_WARNING, LEVEL_DEGRADED, LEVEL_CRITICAL, LEVEL_FATAL,
    level_name,
)


class App:
    def __init__(self):
        # LEDs should come up early so we can signal errors immediately
        self.red_led = LED(config.RED_LED_PIN, active_high=config.LED_ACTIVE_HIGH)
        self.green_led = LED(config.GREEN_LED_PIN, active_high=config.LED_ACTIVE_HIGH)
        self.safe = SafeModeManager(self.red_led)

        self.experiment_running = False
        self.last_sample_ms = time.ticks_ms()

        # --- Button (should almost never fail) ---
        try:
            self.button = Button(
                pin_num=config.BUTTON_PIN,
                pull=config.BUTTON_PULL,
                active_level=config.BUTTON_ACTIVE_LEVEL,
                debounce_ms=config.BUTTON_DEBOUNCE_MS,
            )
        except Exception as e:
            # If button init fails, that's serious but we can still run "always on"
            self.safe.set_error(LEVEL_DEGRADED, "button_init", e)
            self.button = None

        # --- I2C ---
        try:
            self.i2c = I2C(
                config.I2C_ID,
                sda=Pin(config.I2C_SDA),
                scl=Pin(config.I2C_SCL),
                freq=config.I2C_FREQ,
            )
        except Exception as e:
            # Without I2C, OLED+sensor+RTC are gone => critical
            self.safe.set_error(LEVEL_CRITICAL, "i2c_init", e)
            self.i2c = None

        # --- OLED / UI ---
        self.ui_ok = False
        self.oled = None
        self.ui = None
        if self.i2c:
            try:
                self.oled = SSD1306_I2C(
                    config.OLED_WIDTH,
                    config.OLED_HEIGHT,
                    self.i2c,
                    addr=config.OLED_I2C_ADDR,
                )
                self.ui = Ui(self.oled)
                self.ui_ok = True
            except Exception as e:
                self.safe.set_error(LEVEL_CRITICAL, "oled_init", e)
                self.ui_ok = False

        # --- Sensor ---
        self.sensor_ok = False
        self.sensor = None
        if self.i2c:
            try:
                self.sensor = SHT31(self.i2c, addr=config.SHT31_ADDR)
                self.sensor_ok = True
            except Exception as e:
                self.safe.set_error(LEVEL_DEGRADED, "sht31_init", e)
                self.sensor_ok = False

        # --- RTC ---
        self.rtc_ok = False
        self.rtc = None
        self.time = None
        if self.i2c:
            try:
                self.rtc = DS3231(self.i2c, address=config.DS3231_ADDR)
                self.time = Timekeeper(self.rtc)
                # quick read to confirm it responds
                _ = self.rtc.datetime()
                self.rtc_ok = True
            except Exception as e:
                self.safe.set_error(LEVEL_DEGRADED, "rtc_init", e)
                self.rtc_ok = False
                self.time = None

        # --- SD logger ---
        self.sd_logger = SdLogger(mount_point=config.SD_MOUNT_POINT)
        self.sd_ok = False
        self._init_sd()

        # Show something at boot
        self._safe_ui_update(where="boot")

    def _init_sd(self):
        try:
            self.spi = SPI(
                config.SD_SPI_ID,
                baudrate=config.SD_BAUDRATE,
                polarity=0,
                phase=0,
                sck=Pin(config.SD_SCK),
                mosi=Pin(config.SD_MOSI),
                miso=Pin(config.SD_MISO),
            )
            self.sd_cs = Pin(config.SD_CS, Pin.OUT)
            sd = SDCard(self.spi, self.sd_cs, baudrate=config.SD_BAUDRATE)

            ok = self.sd_logger.mount(sd)
            self.sd_ok = bool(ok)
            if not self.sd_ok:
                raise OSError("SD mount failed")
        except Exception as e:
            # SD is optional => warning (logging disabled)
            self.safe.set_error(LEVEL_WARNING, "sd_init", e)
            self.sd_ok = False

    def _utc_iso(self):
        # If RTC fails, fallback to uptime-based timestamp
        if self.time:
            try:
                return self.time.utc_iso()
            except Exception as e:
                self.safe.set_error(LEVEL_DEGRADED, "rtc_read", e)

        # fallback: ticks_ms
        ms = time.ticks_ms()
        return "UPTIME_%dms" % ms

    def _safe_ui_update(self, where=""):
        """
        Always try to show safe-mode info if there's an error.
        Never allow OLED rendering to crash the app.
        """
        if not self.ui_ok:
            return

        if self.safe.level == LEVEL_OK:
            return

        try:
            self.ui.show_error(
                level_name(self.safe.level),
                (where or self.safe.last_error_where)[:16],
                self.safe.last_error_type,
                self.safe.last_error_msg,
            )
        except Exception as e:
            # If UI update fails, we go headless
            self.safe.set_error(LEVEL_CRITICAL, "oled_render", e)
            self.ui_ok = False

    def _set_off_state(self):
        # stop logging safely
        if self.experiment_running:
            try:
                self.sd_logger.stop()
            except Exception as e:
                self.safe.set_error(LEVEL_WARNING, "log_stop", e)

        self.experiment_running = False

        # LEDs
        try:
            self.red_led.on()
            self.green_led.off()
        except Exception as e:
            self.safe.set_error(LEVEL_DEGRADED, "led_off_state", e)

        # UI
        utc_iso = self._utc_iso()
        if self.ui_ok:
            try:
                self.ui.show_off(utc_iso)
            except Exception as e:
                self.safe.set_error(LEVEL_CRITICAL, "oled_show_off", e)
                self.ui_ok = False

    def _set_on_state(self):
        if not self.experiment_running:
            utc_iso = self._utc_iso()
            if self.sd_ok:
                try:
                    self.sd_logger.start_new(utc_iso)
                except Exception as e:
                    # keep running without logging
                    self.safe.set_error(LEVEL_WARNING, "log_start", e)
                    self.sd_ok = False
            self.experiment_running = True

        # LEDs
        try:
            self.green_led.on()
            # red LED is controlled by safe-mode blinker tick; don’t force off here
        except Exception as e:
            self.safe.set_error(LEVEL_DEGRADED, "led_on_state", e)

    def _button_on(self) -> bool:
        # if button missing/broken, default to OFF (safer) unless you prefer always-on
        if not self.button:
            return False
        try:
            return self.button.is_active()
        except Exception as e:
            self.safe.set_error(LEVEL_DEGRADED, "button_read", e)
            return False

    def _read_sensor(self):
        if not self.sensor:
            return None, None
        try:
            return self.sensor.read()
        except Exception as e:
            self.safe.set_error(LEVEL_DEGRADED, "sht31_read", e)
            return None, None

    def _log_row(self, utc_iso, temp_c, rh):
        if not (self.sd_ok and self.experiment_running):
            return
        try:
            self.sd_logger.write_row(utc_iso, temp_c, rh)
        except Exception as e:
            self.safe.set_error(LEVEL_WARNING, "log_write", e)
            # disable further SD attempts this session
            self.sd_ok = False

    def _show_on(self, temp_c, rh, utc_iso):
        if not self.ui_ok:
            return
        try:
            if temp_c is None or rh is None:
                # show degraded info
                self.ui.show_error(
                    level_name(max(self.safe.level, LEVEL_DEGRADED)),
                    "sensor",
                    "SHT31",
                    "read failed",
                )
            else:
                self.ui.show_on(temp_c, rh, utc_iso)
        except Exception as e:
            self.safe.set_error(LEVEL_CRITICAL, "oled_show_on", e)
            self.ui_ok = False

    def run(self):
        # Initial OFF screen
        self._set_off_state()

        while True:
            # Always tick safe-mode LED pattern
            try:
                self.safe.tick_blink()
            except Exception:
                # if blinking fails, nothing else to do; avoid crashing loop
                pass

            on = self._button_on()

            if not on:
                self._set_off_state()
                # if there’s an active error, show it
                self._safe_ui_update(where="off_loop")
                time.sleep_ms(50)
                continue

            # ON state
            self._set_on_state()

            now = time.ticks_ms()
            if time.ticks_diff(now, self.last_sample_ms) >= config.SAMPLE_INTERVAL_MS:
                self.last_sample_ms = now

                temp_c, rh = self._read_sensor()
                utc_iso = self._utc_iso()

                # log only if we have valid numbers
                if temp_c is not None and rh is not None:
                    self._log_row(utc_iso, temp_c, rh)

                # UI update (or safe mode screen)
                self._show_on(temp_c, rh, utc_iso)

                # show error details if we’re in safe mode
                self._safe_ui_update(where="on_loop")

            time.sleep_ms(10)
