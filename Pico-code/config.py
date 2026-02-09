# config.py - central hardware + app settings for Pico project

# OLED
OLED_WIDTH = 128
OLED_HEIGHT = 64
OLED_I2C_ADDR = 0x3C

# I2C bus (OLED + SHT31 + DS3231)
I2C_ID = 0
I2C_SDA = 0
I2C_SCL = 1
I2C_FREQ = 400_000

# SHT31
SHT31_ADDR = 0x44

# DS3231
DS3231_ADDR = 0x68

# Button / switch
BUTTON_PIN = 15
BUTTON_PULL = "down"          # "down" or "up"
BUTTON_ACTIVE_LEVEL = 1       # 0 if switch pulls pin low when ON; 1 if pulls high when ON
BUTTON_DEBOUNCE_MS = 50       # keep small, you already have a stable switch

# LEDs
RED_LED_PIN = 17
GREEN_LED_PIN = 16
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
SAMPLE_INTERVAL_MS = 1000      # sensor read & log interval while ON
