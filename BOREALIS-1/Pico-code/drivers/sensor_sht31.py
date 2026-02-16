import time


class SHT31:
    def __init__(self, i2c, addr=0x44):
        self.i2c = i2c
        self.addr = addr

    def read(self):
        # Single shot, high repeatability, clock stretching disabled (0x2400)
        self.i2c.writeto(self.addr, b"\x24\x00")
        time.sleep_ms(15)

        data = self.i2c.readfrom(self.addr, 6)
        if len(data) != 6:
            raise RuntimeError("SHT31 read error")

        t_raw = (data[0] << 8) | data[1]
        rh_raw = (data[3] << 8) | data[4]

        temp_c = -45 + (175 * t_raw / 65535.0)
        rh = 100 * rh_raw / 65535.0
        return temp_c, rh
