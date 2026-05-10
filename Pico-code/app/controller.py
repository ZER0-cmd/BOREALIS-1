import time
from machine import Pin, I2C, SPI, reset
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
    SENSOR_TEMP,
    SENSOR_MAGNET,
    SENSOR_NAMES
)

class core:
    def __init__(self):
        self.status_led = LED(
            config.STATUS_LED_PIN,
            active_high=config.LED_ACTIVE_HIGH
        )
        
        self.reset1 = Pin(config.RESET1_PIN, Pin.IN, Pin.PULL_DOWN),
        self.reset2 = Pin(config.RESET2_PIN, Pin.IN, Pin.PULL_DOWN),

        # OLED / RTC bus
        self.i2c = I2C(
            config.I2C_ID,
            sda=Pin(config.I2C_SDA),
            scl=Pin(config.I2C_SCL),
            freq=config.I2C_FREQ,
        )

        self.oled = None

        self.sd_detect = SdDetect(
            config.SD_DETECT_PIN,
            active_low=config.SD_DETECT_ACTIVE_LOW
        )
        self.sd = None

        self.sensor_manager = SensorManager()
        self.last_sensor_read_ms = 0

        self.log_ready = False
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

    def oledmanager(self):
        if config.OLED_I2C_ADDR in self.i2c.scan():
            if self.oled == None:
                self.oled = SSD1306_I2C(
                    config.OLED_WIDTH,
                    config.OLED_HEIGHT,
                    self.i2c,
                    addr=config.OLED_I2C_ADDR,
                )
                
        else:
            self.oled = None
        
        self.ui = Ui(self.oled)

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
                self.ui.show_sensor_connected(SENSOR_NAMES[kind])
                self.oled.show()
                time.sleep_ms(config.SENSOR_ANNOUNCE_MS)

        now = time.ticks_ms()
        if time.ticks_diff(now, self.last_sensor_read_ms) >= config.SENSOR_READ_INTERVAL_MS:
            self.last_sensor_read_ms = now

            self.data = self.sensor_manager.read_data()

            if self.data is None:
                self.ui.show_sensor_disconnected()
            else:

                if self.data["kind"] == SENSOR_HUMIDITY:
                    self.datakeys = ["humidity_percent"]
                    show = self.ui.show_humidity_data

                elif self.data["kind"] == SENSOR_PRESSURE:
                    self.datakeys = ["pressure_hpa"]
                    show = self.ui.show_pressure_data

                elif self.data["kind"] == SENSOR_MPU6500:
                    self.datakeys = [
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
                
                elif self.data["kind"] == SENSOR_GAS:
                    self.datakeys = ["alcohol"]
                    show = self.ui.show_gas_data
                
                elif self.data["kind"] == SENSOR_LIGHT:
                    self.datakeys = ["uvindex"]
                    show = self.ui.show_light_data
                
                elif self.data["kind"] == SENSOR_MAGNET:
                    self.datakeys = ['x', 'y', 'z']
                    show = self.ui.show_magnet_data

                else:
                    show = self.ui.show_unknown_sensor(self.data['adc'])
                    return

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
                self.log_ready = True
            except Exception as e:
                self.oled.text("SD: Failed", 0, 55)
                self.log_ready = False
            time.sleep(0.5)
        elif self.inserted:
            self.log_ready = True
            self.oled.text("SD: Inserted", 0, 55)
        else:
            self.sd = None
            self.log_ready = False
            self.oled.text("SD: Not found", 0, 55)
        self.oled.show()
        time.sleep_ms(100)

class library(core):
    def __init__(self):
        core.__init__(self)
        self.file = None
        self.cshift = 0
        self.cscale = 1
        self.filter = None
    
    def resetmanager(self):
        def trigger():
            return self.reset1 == 1 or self.reset2 == 1
        if trigger:
            for i in range(10):
                time.sleep(0.2)
                if not trigger():
                    for i in range(100):
                        if trigger():
                            self.newfile(config.DEFAULT_FILE_NAME)
                        time.sleep(0.1)
                    return
                reset()

    def read_sensor(self, filter=None):
        self.filter = filter
        if filter == None:
            filter = self.datakeys
        filter = list(filter)
        if self.data is not None:
            return [self.data[k] * self.cscale[k] + self.cshift[k] for k in filter]

    def run(self, setup, loop):
        self.oledmanager()
        self.ui.show_boot()
        self.oled.show()
        system_ok = self._run_startup_checks()
        self._show_check_result(system_ok)
        self.experimentmanager()
        # while not self.log_ready:
        #     self.resetmanager()
        #     self.sdmanager()

        setup()

        while True:
            self.resetmanager()
            self.oledmanager()

            self.experimentmanager()
            self.sdmanager()
            loop()
    
    def newfile(self, path=config.DEFAULT_FILE_NAME):
        '''
        If log_ready creates a new file at path adn load it
        '''
        if self.log_ready:
            self.file = logging.newfile(self.sd, path)
    
    def loadfile(self, path):
        '''
        If log_ready loads existing file at path
        '''
        if self.log_ready:
            self.file = logging.loadfile(self.sd, path)
        
    def log_data(self, data):
        '''
        If log_ready logs data in the loaded file
        '''
        if self.file is not None and self.log_ready:
            for i in range(20):
                try:
                    self.file.write_row(data)
                    break
                except Exception as e:
                    print(e)
                    time.sleep_ms(50)

    def log_headers(self, headers=None):
        '''
        If log_ready creates headers (names measured quantities) in the loaded file
        '''
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
                        
    def calibrate(self, value, value2=None, le=50):
        if self.data is None or self.data['kind'] == SENSOR_UNKNOWN:
            self.ui.show_calibration_abort(f'Cannot calibrate\nsensor')
            return
        filter = self.filter
        if filter is None:
            filter = self.datakeys
        try:
            # First measurement set (e.g., low reference)
            acc1 = [0.0 for _ in filter]
            for i in range(le):
                self.oledmanager
                self.resetmanager()
                data = self.sensor_manager.read_data()
                # incremental average
                acc1 = [(a + data[k]) / (i+1) for a, k in zip(acc1, filter)]

            if value2 is not None:
                input('Change to value2. Then hit any button')
                # Second measurement set (e.g., high reference)
                acc2 = [0.0 for _ in filter]
                for i in range(le):
                    self.oledmanager
                    self.resetmanager()
                    data = self.sensor_manager.read_data()
                    acc2 = [(a + data[k]) / (i+1) for a, k in zip(acc2, filter)]

                # Two‑point calibration: compute scale and offset for each channel
                # Calibrated = raw * scale + offset
                # value = acc1 * scale + offset
                # value2 = acc2 * scale + offset
                v1_list = list(value) if hasattr(value, '__iter__') else [value]
                v2_list = list(value2) if hasattr(value2, '__iter__') else [value2]
                self.cscale = [(v2 - v1) / (a2 - a1) for v1, v2, a1, a2 in zip(v1_list, v2_list, acc1, acc2)]
                self.cshift = [v1 - a1 * s for v1, a1, s in zip(v1_list, acc1, self.cscale)]
            else:
                # One‑point calibration: assume scale = 1, compute only offset
                v_list = list(value) if hasattr(value, '__iter__') else [value]
                self.cscale = dict(zip(filter, [1.0] * len(v_list)))
                self.cshift = dict(zip(filter, [v - a for v, a in zip(v_list, acc1)]))

        except Exception as e:
            print('Calibration failed:', e)