from machine import Pin, I2C
import config

i2c = I2C(config.I2C_ID, sda=Pin(config.I2C_SDA), scl=Pin(config.I2C_SCL), freq=config.I2C_FREQ)
addrs = i2c.scan()

print("I2C devices:", [hex(a) for a in addrs])
