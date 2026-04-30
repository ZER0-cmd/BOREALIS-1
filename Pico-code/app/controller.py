import time
from machine import Pin, I2C, SPI
from app.reset_manager import ResetManager
import config
from drivers.display_ssd1306 import SSD1306_I2C
from drivers.output_led import LED
from drivers.sd_detect import SdDetect
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
    SENSOR_TEMP
)


class core:
    def __init__(self):
        self.status_led = LED(
            config.STATUS_LED_PIN,
            active_high=config.LED_ACTIVE_HIGH
        )

        self.reset_manager = ResetManager(
        Pin(config.RESET1_PIN, Pin.IN, Pin.PULL_DOWN),
        Pin(config.RESET2_PIN, Pin.IN, Pin.PULL_DOWN),
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
        self.sd = None

        self.sensor_manager = SensorManager()
        self.last_sensor_read_ms = 0

        self.ready = False
        self.data = {}
        self.datakeys = []

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

    def _sensor_name(self, kind):
        if kind == SENSOR_HUMIDITY:
            return "Humidity sensor"
        if kind == SENSOR_PRESSURE:
            return "Pressure sensor"
        if kind == SENSOR_MPU6500:
            return "MPU6500"
        if kind == SENSOR_UNKNOWN:
            return "Unknown sensor"
        return "No sensor"

    def experimentmanager(self):
        self.changed, kind, adc_value = self.sensor_manager.refresh_connection()

        if self.changed:
            if kind == SENSOR_NONE:
                self.ui.show_sensor_disconnected()
                self.oled.show()
                time.sleep_ms(config.SENSOR_ANNOUNCE_MS)
            elif kind == SENSOR_UNKNOWN:
                self.ui.show_unknown_sensor(adc_value)
                self.oled.show()
                time.sleep_ms(config.SENSOR_ANNOUNCE_MS)
            else:
                self.ui.show_sensor_connected(self._sensor_name(kind), kind)
                self.oled.show()
                time.sleep_ms(config.SENSOR_ANNOUNCE_MS)

        now = time.ticks_ms()
        if time.ticks_diff(now, self.last_sensor_read_ms) >= config.SENSOR_READ_INTERVAL_MS:
            self.last_sensor_read_ms = now

            self.data = self.sensor_manager.read_data()

            self.datakeys = []

            if self.data is None:
                self.ui.show_sensor_disconnected()

            elif self.data["kind"] == SENSOR_UNKNOWN:
                self.ui.show_unknown_sensor(self.data["adc"])

            elif self.data["kind"] == SENSOR_HUMIDITY:
                self.datakeys = ["temperature_c", "humidity_percent"]
                show = self.ui.show_humidity_data

            elif self.data["kind"] == SENSOR_PRESSURE:
                self.datakeys = ["temperature_c", "pressure_hpa"]
                show = self.ui.show_pressure_data

            elif self.data["kind"] == SENSOR_MPU6500:
                self.datakeys = [
                    "temperature_c",
                    "ax_g", "ay_g", "az_g",
                    "gx_dps", "gy_dps", "gz_dps"
                ]
                show = self.ui.show_mpu6500_data
            
            elif self.data["kind"] == SENSOR_SOLAR:
                self.datakeys = ['voltage']
                show = self.ui.show_solar_data

            elif self.data["kind"] == SENSOR_TEMP:
                self.datakeys = ["temperature_c"]
                show = self.ui.show_temp_data
            
            else:
                show = self.ui.show_unknown_sensor

            show(*(self.data[k] for k in self.datakeys))
    
    def sdmanager(self):
        self.inserted = self.sd_detect.is_inserted()
        
        # self.oled.fill(0)
        # self.oled.text("Borealis", 0, 0)
        # self.oled.text("microSD detect:", 0, 16)
        # self.oled.text("INSERTED" if inserted else "NOT INSERTED", 0, 30)
        # # self.oled.text("RAW: %d" % self.sd_detect.raw(), 0, 46)

        if self.inserted and (self.changed or self.sd is None):
            try:
                self.sd = logging.SDCard(SPI(config.SD_SPI_ID, config.SD_BAUDRATE, polarity=0, phase=0, sck=Pin(config.SD_SCK), mosi=Pin(config.SD_MOSI), miso=Pin(config.SD_MISO)), cs=Pin(config.SD_CS))
                self.oled.text('SD: Initialized', 0, 55)
                self.ready = True
            except Exception as e:
                self.oled.text("SD: Failed", 0, 55)
                self.ready = False
            time.sleep(0.5)
        elif self.inserted:
            self.ready = True
            self.oled.text("SD: Inserted", 0, 55)
        else:
            self.sd = None
            self.ready = False
            self.oled.text("SD: Not found", 0, 55)
        self.oled.show()
        time.sleep_ms(100)

    def resetmanager(self):
        if self.reset_manager.is_triggered():
                self.ui.show_resetting()
                self.oled.show()
                self.reset_manager.perform_reset(self.sd)

class library(core):
    def __init__(self):
        core.__init__(self)
        self.file = None

    def read_sensor(self, filter=None):
        if filter == None:
            filter = self.datakeys
        filter = list(filter)
        return [self.data[k] for k in filter]

    def run(self, setup, loop):
        self.ui.show_boot()
        self.oled.show()
        system_ok = self._run_startup_checks()
        self._show_check_result(system_ok)
        self.experimentmanager()
        # while not self.ready:
        #     self.resetmanager()
        #     self.sdmanager()

        setup()

        while True:
            self.resetmanager()

            self.experimentmanager()
            self.sdmanager()
            loop()
    
    def newfile(self, path):
        if self.ready:
            self.file = logging.newfile(self.sd, path)
    
    def loadfile(self, path):
        if self.ready:
            self.file = logging.loadfile(self.sd, path)
        
    def log_data(self, data):
        if self.file is not None and self.ready:
            for i in range(20):
                try:
                    self.file.write_row(data)
                    break
                except Exception as e:
                    print(e)
                    time.sleep_ms(50)

    def log_headers(self, headers=None):
        if self.file is not None and self.ready:
            for i in range(20):
                try:
                    if headers is None:
                        headers = self.datakeys
                    self.file.write_headers(headers)
                    break
                except Exception as e:
                    print(e)
                    time.sleep_ms(50)