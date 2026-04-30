# config.py - central hardware + app settings for Pico project

# OLED
OLED_WIDTH = 128
OLED_HEIGHT = 64
OLED_I2C_ADDR = 0x3C
OLED_SPLASH_MS = 3000

# OLED / RTC bus
# GP0 = SDA, GP1 = SCL
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

# One status LED
STATUS_LED_PIN = 2
LED_ACTIVE_HIGH = True

# SD Card (SPI1)
SD_SPI_ID = 1
SD_SCK = 10
SD_MOSI = 11 #RX
SD_MISO = 8 #TX
SD_CS = 9
SD_BAUDRATE = 1_000_000
SD_MOUNT_POINT = "/sd"

# Sampling / UI update
SAMPLE_INTERVAL_MS = 1000

# Sensor identification ADC
SENSOR_ID_ADC_PIN = 28

# Sensor bus (from your working test scripts)
SENSOR_I2C_ID = 1
SENSOR_I2C_SDA = 14
SENSOR_I2C_SCL = 15
SENSOR_I2C_FREQ = 100_000

# ADC bus (i2c0 on schematic)
ADC_I2C_ID = 0
ADC_I2C_SDA = 0
ADC_I2C_SCL = 1
ADC_I2C_FREQ = 100_1000

'''
CO2 | 680 Ω
BAR | 510 Ω
light | 750 Ω
GAS | 560 Ω
HUM | 1.1 kΩ
VOLT | 820 Ω
TEMP | 1.2 kΩ
MAG | 910 Ω
ACL | 620 Ω

Formula:
V = 6.6e7 / (R + 1000)

def sid(l: list):
    import numpy as np
    v = lambda r: int(6.6e7 / (r + 1000))
    n = len(l)
    
    li = sorted([(val, i + 1) for i, val in enumerate(l)])
    
    q = np.zeros((5, n+1), dtype=int)
    
    for i, (val, id) in enumerate(li):
        vol = v(val)
        q[0, i] = vol
        q[1, i] = vol
        q[2, i] = id
        q[3, i] = vol
        q[4, i] = val
        
    for i in range(n):
        m = (q[0, i] + q[1, i+1]) // 2
        q[0, i] = m
        q[1, i+1] = m
        
    result = q.T
    
    result = result[result[:, 2].argsort()]
    
    print(result)

sid([680,510,750,560,1100,820,1200,910,620])
'''

# Sensor ID ranges
SENSOR_NONE_ID = [0, 300]
SENSOR_CO2_ID = [38499, 400012]
SENSOR_PRESSURE_ID = [43007, 43708]
SENSOR_LIGHT_ID = [36988, 38499]
SENSOR_GAS_ID = [41523, 43007]
SENSOR_HUMIDITY_ID = [30714, 32991]
SENSOR_SOLAR_ID = [35408, 36988]
SENSOR_TEMP_ID = [28000, 30714]
SENSOR_MAGNETOMETER_ID = [32991, 35408]
SENSOR_MPU6500_ID = [40012, 41523]


# Timing
SENSOR_ANNOUNCE_MS = 2000
SENSOR_READ_INTERVAL_MS = 1000

# Reset pin
RESET1_PIN = 17
RESET2_PIN = 6