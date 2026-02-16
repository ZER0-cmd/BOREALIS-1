class DS3231:
    def __init__(self, i2c, address=0x68):
        self.i2c = i2c
        self.address = address

    def _bcd2dec(self, b):
        return (b >> 4) * 10 + (b & 0x0F)

    def _dec2bcd(self, d):
        return ((d // 10) << 4) | (d % 10)

    def datetime(self, dt=None):
        """
        If dt is None: return (year, month, day, weekday, hour, minute, second, subseconds)
        If dt is provided: set time from that tuple.
        """
        if dt is None:
            data = self.i2c.readfrom_mem(self.address, 0x00, 7)

            sec = self._bcd2dec(data[0] & 0x7F)
            minute = self._bcd2dec(data[1] & 0x7F)
            hour = self._bcd2dec(data[2] & 0x3F)
            weekday = self._bcd2dec(data[3] & 0x07)
            day = self._bcd2dec(data[4] & 0x3F)
            month = self._bcd2dec(data[5] & 0x1F)
            year = self._bcd2dec(data[6]) + 2000

            return (year, month, day, weekday, hour, minute, sec, 0)

        (year, month, day, weekday, hour, minute, second, subsec) = dt
        year -= 2000

        buf = bytearray(7)
        buf[0] = self._dec2bcd(second)
        buf[1] = self._dec2bcd(minute)
        buf[2] = self._dec2bcd(hour)
        buf[3] = self._dec2bcd(weekday if weekday else 1)
        buf[4] = self._dec2bcd(day)
        buf[5] = self._dec2bcd(month)
        buf[6] = self._dec2bcd(year)

        self.i2c.writeto_mem(self.address, 0x00, buf)
