import time #morbing time 
from machine import Pin, I2C

import config
from drivers.display_ssd1306 import SSD1306_I2C
from drivers.output_led import LED
from app.ui import Ui


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

        # Optional: check that OLED is actually present
        addrs = self.i2c.scan()
        if config.OLED_I2C_ADDR not in addrs:
            raise OSError("OLED not found at address 0x%02X. Found: %s" % (
                config.OLED_I2C_ADDR,
                [hex(a) for a in addrs]
            ))

        self.oled = SSD1306_I2C(
            config.OLED_WIDTH,
            config.OLED_HEIGHT,
            self.i2c,
            addr=config.OLED_I2C_ADDR,
        )
        self.ui = Ui(self.oled)

    def run(self):
        # Boot splash
        self.ui.show_boot()
        self.green_led.on()
        time.sleep_ms(config.OLED_SPLASH_MS)

        # Idle screen
        self.ui.show_idle()

        while True:
            time.sleep_ms(200)
