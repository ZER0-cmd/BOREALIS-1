# drivers/rtc_ds1302.py

from machine import Pin

_REG_SECOND  = 0x80
_REG_MINUTE  = 0x82
_REG_HOUR    = 0x84
_REG_DATE    = 0x86
_REG_MONTH   = 0x88
_REG_WEEKDAY = 0x8A
_REG_YEAR    = 0x8C
_REG_WP      = 0x8E


def _bcd_dec(bcd):
    return (bcd >> 4) * 10 + (bcd & 0x0F)


def _dec_bcd(dec):
    return ((dec // 10) << 4) | (dec % 10)


class DS1302:
    """
    Driver for the DS1302Z+ real-time clock.

    3-wire interface: CLK (output), DAT (bidirectional), CE (output, active-high).
    Accepts either Pin objects or bare GPIO numbers.

    datetime() returns and accepts an 8-tuple identical in layout to the DS3231
    driver this replaces:
        (year, month, day, weekday, hour, minute, second, subseconds)
    weekday is 1–7 where 1 = Monday, matching the controller's _dt_to_epoch().
    subseconds is always 0 on read (DS1302 has no sub-second register).
    """

    def __init__(self, clk, dat, ce):
        self._clk = clk if isinstance(clk, Pin) else Pin(clk, Pin.OUT)
        self._dat = dat if isinstance(dat, Pin) else Pin(dat, Pin.OUT)
        self._ce  = ce  if isinstance(ce,  Pin) else Pin(ce,  Pin.OUT)
        self._clk.init(Pin.OUT)
        self._ce.init(Pin.OUT)
        self._clk.value(0)
        self._ce.value(0)

    # ------------------------------------------------------------------
    # Low-level bit-bang
    # ------------------------------------------------------------------

    def _write_byte(self, byte):
        self._dat.init(Pin.OUT)
        for _ in range(8):
            self._dat.value(byte & 0x01)
            self._clk.value(1)
            self._clk.value(0)
            byte >>= 1

    def _read_byte(self):
        self._dat.init(Pin.IN)
        byte = 0
        for i in range(8):
            byte |= self._dat.value() << i
            self._clk.value(1)
            self._clk.value(0)
        return byte

    def _read_reg(self, reg):
        self._ce.value(1)
        self._write_byte(reg | 0x01)
        value = self._read_byte()
        self._ce.value(0)
        return value

    def _write_reg(self, reg, value):
        self._ce.value(1)
        self._write_byte(reg & 0xFE)
        self._write_byte(value)
        self._ce.value(0)

    # ------------------------------------------------------------------
    # Write-protect
    # ------------------------------------------------------------------

    def _wp(self, enable):
        self._write_reg(_REG_WP, 0x80 if enable else 0x00)

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def datetime(self, dt=None):
        """
        Get or set the date/time.

        Read  → returns (year, month, day, weekday, hour, minute, second, 0)
        Write → pass the same 8-tuple as dt=; returns None.
        """
        if dt is not None:
            year, month, day, weekday, hour, minute, second, _ = dt
            self._wp(False)
            self._write_reg(_REG_SECOND,  _dec_bcd(second)  & 0x7F)  # bit 7 = halt; keep clear
            self._write_reg(_REG_MINUTE,  _dec_bcd(minute))
            self._write_reg(_REG_HOUR,    _dec_bcd(hour)    & 0x3F)  # bit 6 = 12h; keep clear → 24h
            self._write_reg(_REG_DATE,    _dec_bcd(day))
            self._write_reg(_REG_MONTH,   _dec_bcd(month))
            self._write_reg(_REG_WEEKDAY, _dec_bcd(weekday))
            self._write_reg(_REG_YEAR,    _dec_bcd(year % 100))
            self._wp(True)
            return

        second  = _bcd_dec(self._read_reg(_REG_SECOND)  & 0x7F)
        minute  = _bcd_dec(self._read_reg(_REG_MINUTE)  & 0x7F)
        hour    = _bcd_dec(self._read_reg(_REG_HOUR)    & 0x3F)
        day     = _bcd_dec(self._read_reg(_REG_DATE)    & 0x3F)
        month   = _bcd_dec(self._read_reg(_REG_MONTH)   & 0x1F)
        weekday = _bcd_dec(self._read_reg(_REG_WEEKDAY) & 0x07)
        year    = _bcd_dec(self._read_reg(_REG_YEAR))   + 2000

        return (year, month, day, weekday, hour, minute, second, 0)