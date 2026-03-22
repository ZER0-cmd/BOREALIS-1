import time
from machine import Pin, I2C, SPI

import config
from drivers.display_ssd1306 import SSD1306_I2C
from drivers.output_led import LED
from drivers.sd_detect import SdDetect
from app.ui import Ui
from app.logging import SDlogger


class App:
    def __init__(self):
        self.red_led = LED(config.RED_LED_PIN, active_high=config.LED_ACTIVE_HIGH)
        self.green_led = LED(config.GREEN_LED_PIN, active_high=config.LED_ACTIVE_HIGH)

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

        # microSD detect input
        self.sd_detect = SdDetect(
            config.SD_DETECT_PIN,
            active_low=config.SD_DETECT_ACTIVE_LOW
        )
        self.sd = None

    def run(self):
        self.green_led.on()

        # Splash screen
        self.ui.show_boot("pictures/logo.csv")
        time.sleep_ms(config.OLED_SPLASH_MS)
        # Live detect test screen
        while True:
            inserted = self.sd_detect.is_inserted()
            
            self.oled.fill(0)
            self.oled.text("Borealis", 0, 0)
            self.oled.text("microSD detect:", 0, 16)
            self.oled.text("INSERTED" if inserted else "NOT INSERTED", 0, 30)
            # self.oled.text("RAW: %d" % self.sd_detect.raw(), 0, 46)

            if inserted and self.sd is None:
                try:
                    self.sd = SDlogger(SPI(config.SD_SPI_ID, config.SD_BAUDRATE, polarity=0, phase=0, sck=Pin(config.SD_SCK), mosi=Pin(config.SD_MOSI), miso=Pin(config.SD_MISO)),
                                       cs=Pin(config.SD_CS),
                                       mount=config.SD_MOUNT_POINT)
                    self.oled.text('Status: Initialized', 0, 46)
                except Exception as e:
                    self.oled.text("Status: Failed", 0, 46)
                time.sleep(0.5)
            elif inserted:
                self.sd.write_row((1,2,3,4))
                self.oled.text("Status: Writing", 0, 46)
            else:
                self.sd = None
                self.oled.text("Status: Not found", 0, 46)

            self.oled.show()
            time.sleep_ms(200)