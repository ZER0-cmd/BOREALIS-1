# config.py - central hardware + app settings for Pico project

# OLED
OLED_WIDTH = 128
OLED_HEIGHT = 64
OLED_I2C_ADDR = 0x3C
OLED_SPLASH_MS = 3000

# I2C bus (OLED + RTC + future sensors if needed)
# GP0 = SDA, GP1 = SCL  (Pico physical pins 1 and 2)
I2C_ID = 0
I2C_SDA = 0
I2C_SCL = 1
I2C_FREQ = 400_000

# RTC
DS3231_ADDR = 0x68

# microSD detect
SD_DETECT_PIN = 19
SD_DETECT_ACTIVE_LOW = True

# Button / switch
BUTTON_PIN = 15
BUTTON_PULL = "down"
BUTTON_ACTIVE_LEVEL = 1
BUTTON_DEBOUNCE_MS = 50

# Status LED
STATUS_LED_PIN = 2
LED_ACTIVE_HIGH = True

# SD Card (SPI1)
SD_SPI_ID = 1
SD_SCK = 10
SD_MOSI = 11
SD_MISO = 12
SD_CS = 13
SD_BAUDRATE = 1_000_000
SD_MOUNT_POINT = "/sd"

# Sampling / UI update
SAMPLE_INTERVAL_MS = 1000