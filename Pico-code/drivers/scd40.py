import time


class SCD40:
    ADDRESS = 0x62

    CMD_START_PERIODIC_MEASUREMENT = 0x21B1
    CMD_STOP_PERIODIC_MEASUREMENT = 0x3F86
    CMD_READ_MEASUREMENT = 0xEC05
    CMD_GET_DATA_READY_STATUS = 0xE4B8
    CMD_REINIT = 0x3646
    CMD_SOFT_RESET = 0x3632
    CMD_GET_SERIAL_NUMBER = 0x3682

    def __init__(self, i2c, address=ADDRESS):
        self.i2c = i2c
        self.address = address
        self._co2 = None
        self._temperature = None
        self._humidity = None

        devices = self.i2c.scan()
        if self.address not in devices:
            raise OSError("SCD4x not found at 0x{:02X}".format(self.address))

    def _crc8(self, data):
        crc = 0xFF
        for byte in data:
            crc ^= byte
            for _ in range(8):
                if crc & 0x80:
                    crc = ((crc << 1) ^ 0x31) & 0xFF
                else:
                    crc = (crc << 1) & 0xFF
        return crc

    def _write_cmd(self, cmd):
        buf = bytes([(cmd >> 8) & 0xFF, cmd & 0xFF])
        self.i2c.writeto(self.address, buf)

    def _read_words(self, count):
        raw = self.i2c.readfrom(self.address, count * 3)
        words = []
        for i in range(count):
            msb = raw[i * 3]
            lsb = raw[i * 3 + 1]
            crc = raw[i * 3 + 2]
            if self._crc8(bytes([msb, lsb])) != crc:
                raise ValueError("CRC mismatch")
            words.append((msb << 8) | lsb)
        return words

    def stop_periodic_measurement(self):
        self._write_cmd(self.CMD_STOP_PERIODIC_MEASUREMENT)
        time.sleep_ms(500)

    def soft_reset(self):
        self._write_cmd(self.CMD_SOFT_RESET)
        time.sleep_ms(30)

    def reinit(self):
        self._write_cmd(self.CMD_REINIT)
        time.sleep_ms(30)

    def start_periodic_measurement(self):
        self._write_cmd(self.CMD_START_PERIODIC_MEASUREMENT)
        time.sleep_ms(1)

    def get_serial_number(self):
        self._write_cmd(self.CMD_GET_SERIAL_NUMBER)
        time.sleep_ms(1)
        w = self._read_words(3)
        return (w[0] << 32) | (w[1] << 16) | w[2]

    def data_ready(self):
        self._write_cmd(self.CMD_GET_DATA_READY_STATUS)
        time.sleep_ms(1)
        status = self._read_words(1)[0]
        return (status & 0x07FF) != 0

    def read_measurement(self):
        self._write_cmd(self.CMD_READ_MEASUREMENT)
        time.sleep_ms(1)
        w = self._read_words(3)

        co2 = w[0]
        temperature = -45.0 + 175.0 * (w[1] / 65535.0)
        humidity = 100.0 * (w[2] / 65535.0)

        self._co2 = co2
        self._temperature = temperature
        self._humidity = humidity
        return co2, temperature, humidity

    def begin(self):
        # Bring sensor into a known good state
        try:
            self.stop_periodic_measurement()
        except Exception:
            pass
        self.reinit()
        self.start_periodic_measurement()
        time.sleep_ms(5500)

    def read(self, timeout_ms=7000):
        start = time.ticks_ms()
        while not self.data_ready():
            if time.ticks_diff(time.ticks_ms(), start) > timeout_ms:
                raise TimeoutError("SCD4x data not ready")
            time.sleep_ms(200)
        return self.read_measurement()

    @property
    def co2(self):
        return self._co2

    @property
    def temperature(self):
        return self._temperature

    @property
    def humidity(self):
        return self._humidity