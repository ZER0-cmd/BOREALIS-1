import time
from machine import Pin, I2C, SPI, reset
import config
from drivers.display_ssd1306 import SSD1306_I2C
from drivers.output_led import LED
from drivers.sd_detect import SdDetect
from drivers.rtc_ds1302 import DS1302
from app.ui import Ui
from app import logging
from app.sensor_manager import (
    SensorManager,
    SENSOR_NONE,
    SENSOR_HUMIDITY,
    SENSOR_PRESSURE,
    SENSOR_MPU6500,
    SENSOR_UNKNOWN,
    SENSOR_GAS,
    SENSOR_LIGHT,
    SENSOR_SOLAR,
    SENSOR_TEMP,
    SENSOR_MAGNET,
    SENSOR_NAMES,
)


class core:
    def __init__(self):
        self.green_led = LED(
            config.LED_GREEN,
            active_high=config.LED_ACTIVE_HIGH,
        )
        self.blue_led = LED(
            config.LED_BLUE,
            active_high=config.LED_ACTIVE_HIGH,
        )
        self.status_led = LED(
            config.STATUS_LED_PIN,
            active_high=config.LED_ACTIVE_HIGH,
        )
        self.reset1 = Pin(config.RESET1_PIN, Pin.IN, Pin.PULL_DOWN)
        self.reset2 = Pin(config.RESET2_PIN, Pin.IN, Pin.PULL_DOWN)
        self.i2c = I2C(
            config.I2C_ID,
            sda=Pin(config.I2C_SDA),
            scl=Pin(config.I2C_SCL),
            freq=config.I2C_FREQ,
        )
        self.oled = None
        self.sd_detect = SdDetect(
            config.SD_DETECT_PIN,
            active_low=config.SD_DETECT_ACTIVE_LOW,
        )
        self.sd = None
        self.sensor_manager = SensorManager(i2c_adc=self.i2c)
        self.last_sensor_read_ms = 0
        self.log_ready = False
        self.data = {}
        self.datakeys = []
        self.ui = None

        # Synchronisation: flag to signal fresh sensor data
        self._new_data_available = False

        # --- RTC / elapsed-time setup -----------------------------------
        self.start_ticks_ms = time.ticks_ms()
        self.rtc_ok = False
        self.start_epoch = None
        self.rtc = None
        try:
            self.rtc = DS1302(
                Pin(config.DS1302_CLK),
                Pin(config.DS1302_DAT),
                Pin(config.DS1302_CE),
            )
            dt = self.rtc.datetime()
            self.start_epoch = self._dt_to_epoch(dt)
            self.rtc_ok = True
        except Exception as e:
            print("RTC init failed:", e)

    # ------------------------------------------------------------------
    # Time helpers
    # ------------------------------------------------------------------

    @staticmethod
    def _dt_to_epoch(dt):
        year, month, day, weekday, hour, minute, sec, _ = dt
        return time.mktime((year, month, day, hour, minute, sec,
                            (weekday - 1) % 7, 0))

    def _elapsed_s(self):
        ticks_now = time.ticks_ms()
        uptime_s = time.ticks_diff(ticks_now, self.start_ticks_ms) / 1000.0

        if self.rtc_ok:
            try:
                now_epoch = self._dt_to_epoch(self.rtc.datetime())
                rtc_elapsed = now_epoch - self.start_epoch
                if uptime_s > 10 and rtc_elapsed < 1.0:
                    self.rtc_ok = False
                    return uptime_s
                return rtc_elapsed
            except Exception as e:
                print("RTC read failed:", e)
                self.rtc_ok = False

        return uptime_s

    # ------------------------------------------------------------------
    # Startup
    # ------------------------------------------------------------------

    def _run_startup_checks(self):
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

    # ------------------------------------------------------------------
    # Managers
    # ------------------------------------------------------------------

    def oledmanager(self):
        if self.ui is not None:
            self.oled = self.ui.oled
        if self.oled is not None:
            return
        if config.OLED_I2C_ADDR in self.i2c.scan():
            try:
                self.oled = SSD1306_I2C(
                    config.OLED_WIDTH,
                    config.OLED_HEIGHT,
                    self.i2c,
                    addr=config.OLED_I2C_ADDR,
                )
            except Exception as e:
                print("OLED init failed:", e)
                self.oled = None
        self.ui = Ui(self.oled)
        self.oled = self.ui.oled

    def experimentmanager(self):
        self.changed, kind, adc_value = self.sensor_manager.refresh_connection()
        if self.changed:
            if kind == SENSOR_NONE:
                self.ui.show_sensor_disconnected()
                self.ui.show()
                time.sleep_ms(config.SENSOR_ANNOUNCE_MS)
            elif kind == SENSOR_UNKNOWN:
                self.ui.show_unknown_sensor(adc_value)
                self.ui.show()
                time.sleep_ms(config.SENSOR_ANNOUNCE_MS)
            else:
                self.ui.show_sensor_connected(SENSOR_NAMES[kind])
                self.ui.show()
                time.sleep_ms(config.SENSOR_ANNOUNCE_MS)

        now = time.ticks_ms()
        if time.ticks_diff(now, self.last_sensor_read_ms) >= config.SENSOR_READ_INTERVAL_MS:
            self.last_sensor_read_ms = now
            self.data = self.sensor_manager.read_data()
            if self.data is None:
                self.ui.show_sensor_disconnected()
                self._new_data_available = False
                return
            if self.data["kind"] == SENSOR_HUMIDITY:
                sensor_keys = ["humidity_percent"]
                show = self.ui.show_humidity_data
            elif self.data["kind"] == SENSOR_PRESSURE:
                sensor_keys = ["pressure_hpa"]
                show = self.ui.show_pressure_data
            elif self.data["kind"] == SENSOR_MPU6500:
                sensor_keys = ["ax_g", "ay_g", "az_g", "gx_dps", "gy_dps", "gz_dps"]
                show = self.ui.show_mpu6500_data
            elif self.data["kind"] == SENSOR_SOLAR:
                sensor_keys = ["voltage"]
                show = self.ui.show_solar_data
            elif self.data["kind"] == SENSOR_TEMP:
                sensor_keys = ["temperature_c"]
                show = self.ui.show_temp_data
            elif self.data["kind"] == SENSOR_GAS:
                sensor_keys = ["alcohol"]
                show = self.ui.show_gas_data
            elif self.data["kind"] == SENSOR_LIGHT:
                sensor_keys = ["uvindex"]
                show = self.ui.show_light_data
            elif self.data["kind"] == SENSOR_MAGNET:
                sensor_keys = ["B_x", "B_y", "B_z"]
                show = self.ui.show_magnet_data
            else:
                self.ui.show_unknown_sensor(self.data["adc"])
                self._new_data_available = False
                return

            self.data["elapsed_s"] = self._elapsed_s()
            self.datakeys = ["elapsed_s"] + sensor_keys

            show(*(self.data[k] for k in sensor_keys))

            # Mark fresh data as available – only reset when consumed
            self._new_data_available = True

    def sdmanager(self):
        self.inserted = self.sd_detect.is_inserted()
        if self.inserted and (self.changed or self.sd is None):
            try:
                self.sd = logging.SDCard(
                    SPI(
                        config.SD_SPI_ID,
                        config.SD_BAUDRATE,
                        polarity=0,
                        phase=0,
                        sck=Pin(config.SD_SCK),
                        mosi=Pin(config.SD_MOSI),
                        miso=Pin(config.SD_MISO),
                    ),
                    cs=Pin(config.SD_CS),
                )
                self.ui.text("SD: Initialized", 0, 55)
                self.log_ready = True
            except Exception as e:
                self.ui.text("SD: Failed", 0, 55)
                self.log_ready = False
            time.sleep(0.5)
        elif self.inserted:
            self.log_ready = True
            self.ui.text("SD: Inserted", 0, 55)
        else:
            self.sd = None
            self.log_ready = False
            self.ui.text("SD: Not found", 0, 55)
        self.ui.show()
        time.sleep_ms(100)

    def statusmanager(self):
        if self.log_ready:
            self.green_led.on()
        else:
            self.green_led.off()
        if self.rtc_ok:
            self.blue_led.on()
        else:
            self.blue_led.off()
        if self.data is None:
            self.green_led.on(0.65)


class library(core):
    def __init__(self):
        core.__init__(self)
        self.file = None
        self.cshift = None
        self.cscale = None
        self.filter = None

        # Button state machine (double‑click / long‑press)
        self._btn_last_state = False
        self._btn_last_change = 0
        self._btn_press_start = 0
        self._btn_last_release = None

    # ------------------------------------------------------------------
    # Reset / file‑creation manager
    # ------------------------------------------------------------------

    def resetmanager(self):
        now = time.ticks_ms()
        pressed = self.reset1.value() or self.reset2.value()

        if pressed != self._btn_last_state:
            if time.ticks_diff(now, self._btn_last_change) < 30:
                return
            self._btn_last_change = now
            self._btn_last_state = pressed

            if pressed:
                self._btn_press_start = now
                if (self._btn_last_release is not None and
                    time.ticks_diff(now, self._btn_last_release) < 400):
                    if self.log_ready:
                        self.ui.show_newfile(config.DEFAULT_FILE_NAME)
                        self.ui.show()
                        self.newfile(config.DEFAULT_FILE_NAME)
                    self._btn_last_release = None
                return
            else:
                self._btn_last_release = now
                return

        if pressed and time.ticks_diff(now, self._btn_press_start) >= 2000:
            self.ui.show_resetting()
            self.ui.show()
            time.sleep(0.5)
            reset()

    # ------------------------------------------------------------------
    # Blocking sensor read – waits for fresh hardware sample
    # ------------------------------------------------------------------

    def read_sensor(self, filter=None):
        """
        Return the most recent sensor data as a list.
        Blocks until a new sample has been taken by experimentmanager().
        """
        self.filter = filter
        if filter is None:
            filter = self.datakeys
        filter = list(filter)

        # Wait until experimentmanager has set new_data_available
        while not self._new_data_available:
            time.sleep_ms(5)          # yield to background tasks
            self.experimentmanager()  # also updates the flag

        # Consume the fresh data
        try:
            self._new_data_available = False
            if self.data is not None:
                if self.cscale is not None or self.cshift is not None:
                    return [self.data[k] * self.cscale[k] + self.cshift[k] for k in filter]
                return [self.data[k] for k in filter]
        except Exception:
            return None

    # ------------------------------------------------------------------
    # Main run loop
    # ------------------------------------------------------------------

    def run(self, setup, loop):
        self.oledmanager()
        self.ui.show_boot()
        self.ui.show()
        system_ok = self._run_startup_checks()
        self._show_check_result(system_ok)
        self.experimentmanager()
        setup()
        while True:
            self.resetmanager()
            self.oledmanager()
            self.statusmanager()
            self.experimentmanager()   # may set _new_data_available
            self.sdmanager()
            loop()                     # user code calls read_sensor() + logging

    # ------------------------------------------------------------------
    # File helpers
    # ------------------------------------------------------------------

    def newfile(self, path=config.DEFAULT_FILE_NAME):
        if self.log_ready:
            self.file = logging.newfile(self.sd, path)

    def loadfile(self, path):
        if self.log_ready:
            self.file = logging.loadfile(self.sd, path)

    def log_data(self, data):
        if self.file is not None and self.log_ready:
            for i in range(20):
                try:
                    self.file.write_row(data)
                    break
                except Exception as e:
                    print(e)
                    time.sleep_ms(50)

    def log_headers(self, headers=None):
        if self.file is not None and self.log_ready:
            for i in range(20):
                try:
                    if headers is None:
                        headers = self.datakeys
                    self.file.write_headers(headers)
                    break
                except Exception as e:
                    print(e)
                    time.sleep_ms(50)

    # ------------------------------------------------------------------
    # Calibration (unchanged, but safe against None OLED through ui)
    # ------------------------------------------------------------------

    def calibrate(self, value, value2=None, le=50):
        if self.data is None or self.data["kind"] == SENSOR_UNKNOWN:
            self.ui.show_calibration_abort("Cannot calibrate\nsensor")
            return
        filter = self.filter if self.filter is not None else self.datakeys
        filter = list(filter)

        def collect(le):
            acc = [0.0] * len(filter)
            for i in range(le):
                data = self.sensor_manager.read_data()
                if data is None:
                    continue
                for j, k in enumerate(filter):
                    acc[j] += data[k]
            return [a / le for a in acc]

        try:
            acc1 = collect(le)
            if value2 is not None:
                input("Change to value2. Then hit any button")
                acc2 = collect(le)
                v1_list = list(value)  if hasattr(value,  "__iter__") else [value]
                v2_list = list(value2) if hasattr(value2, "__iter__") else [value2]
                scales = [(v2 - v1) / (a2 - a1)
                          for v1, v2, a1, a2 in zip(v1_list, v2_list, acc1, acc2)]
                shifts = [v1 - a1 * s
                          for v1, a1, s in zip(v1_list, acc1, scales)]
            else:
                v_list = list(value) if hasattr(value, "__iter__") else [value]
                scales = [1.0] * len(filter)
                shifts = [v - a for v, a in zip(v_list, acc1)]
            self.cscale = dict(zip(filter, scales))
            self.cshift = dict(zip(filter, shifts))
        except Exception as e:
            print("Calibration failed:", e)

    def write_oled(self, msg):
        self.clear_oled()
        self.ui.text_center(str(msg), 28)

    def clear_oled(self):
        self.ui.clear()