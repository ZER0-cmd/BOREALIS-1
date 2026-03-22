"""Non-blocking MicroPython driver for the Sensirion SCD41 CO2 sensor.

Features:
- Non-blocking single-shot measurement
- No periodic mode
- No long blocking delays

Usage:
    sensor.trigger()
    while not sensor.ready():
        time.sleep_ms(100)
    co2, temp, rh = sensor.read()
"""

try:
    import time
except ImportError:
    import utime as time


class SCD41:
    ADDRESS = 0x62

    CMD_MEASURE_SINGLE_SHOT = 0x219D
    CMD_READ_MEASUREMENT = 0xEC05

    MEASUREMENT_TIME_MS = 5000  # typical measurement time

    def __init__(self, i2c, address=ADDRESS):
        self.i2c = i2c
        self.address = address
        self._cmd = bytearray(2)
        self._buffer = bytearray(9)
        self._crc_buffer = bytearray(2)

        self._measuring = False
        self._start_time = 0

    # ---------- LOW LEVEL ----------

    def _send_command(self, cmd):
        self._cmd[0] = (cmd >> 8) & 0xFF
        self._cmd[1] = cmd & 0xFF
        try:
            self.i2c.writeto(self.address, self._cmd)
        except OSError:
            # Ignore NACK during measurement trigger
            pass

    def _read_reply(self, num):
        self.i2c.readfrom_into(self.address, self._buffer, num)
        self._check_crc(self._buffer[:num])

    def _check_crc(self, buf):
        for i in range(0, len(buf), 3):
            self._crc_buffer[0] = buf[i]
            self._crc_buffer[1] = buf[i + 1]
            if self._crc8(self._crc_buffer) != buf[i + 2]:
                raise RuntimeError("CRC failed")

    @staticmethod
    def _crc8(buffer):
        crc = 0xFF
        for byte in buffer:
            crc ^= byte
            for _ in range(8):
                if crc & 0x80:
                    crc = ((crc << 1) ^ 0x31) & 0xFF
                else:
                    crc = (crc << 1) & 0xFF
        return crc

    # ---------- NON-BLOCKING API ----------

    def trigger(self):
        """Start a measurement (non-blocking)."""
        self._send_command(self.CMD_MEASURE_SINGLE_SHOT)
        self._start_time = time.ticks_ms()
        self._measuring = True

    def ready(self):
        """Check if measurement is finished."""
        if not self._measuring:
            return False
        return time.ticks_diff(time.ticks_ms(), self._start_time) >= self.MEASUREMENT_TIME_MS

    def read(self):
        """Read measurement result (must call after ready())."""
        if not self.ready():
            raise RuntimeError("Measurement not ready")

        # small safety delay
        time.sleep_ms(50)

        self._send_command(self.CMD_READ_MEASUREMENT)
        self._read_reply(9)

        co2 = (self._buffer[0] << 8) | self._buffer[1]

        temp_raw = (self._buffer[3] << 8) | self._buffer[4]
        temp = -45 + 175 * (temp_raw / 65535.0)

        rh_raw = (self._buffer[6] << 8) | self._buffer[7]
        rh = 100 * (rh_raw / 65535.0)

        self._measuring = False
        return co2, temp, rh

    def read_co2(self):
        """Convenience: trigger + wait loop + return CO2 only."""
        self.trigger()
        while not self.ready():
            time.sleep_ms(100)
        co2, _, _ = self.read()
        return co2


# ---------- example ----------

# sensor.trigger()
# while not sensor.ready():
#     time.sleep_ms(100)
# co2, temp, rh = sensor.read()
# print(co2, temp, rh)
