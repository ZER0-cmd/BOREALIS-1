"""
ltr390.py - Minimal MicroPython driver for the LTR390 UV sensor.

Usage example:
    from machine import I2C, Pin
    i2c = I2C(0, scl=Pin(22), sda=Pin(21))
    uv = LTR390(i2c)
    uv.enable_uv()
    print("Raw UV:", uv.read_uv())
    print("UV Index:", uv.uv_index())
"""

from micropython import const

# Register addresses
_LTR390_MAIN_CTRL    = const(0x00)
_LTR390_MEAS_RATE    = const(0x04)
_LTR390_GAIN         = const(0x05)
_LTR390_PART_ID      = const(0x06)
_LTR390_MAIN_STATUS  = const(0x07)
_LTR390_ALS_DATA0    = const(0x0D)   # low byte
_LTR390_ALS_DATA1    = const(0x0E)   # high byte
_LTR390_ALS_DATA2    = const(0x0F)   # extra (20-bit)
_LTR390_UVS_DATA0    = const(0x10)
_LTR390_UVS_DATA1    = const(0x11)
_LTR390_UVS_DATA2    = const(0x12)

# Resolution / integration time mapping (bits -> ms)
_RESOLUTION_TO_MS = {
    0x00: 400,   # 20-bit
    0x01: 200,   # 19-bit
    0x02: 100,   # 18-bit (default)
    0x03: 50,    # 17-bit
    0x04: 25,    # 16-bit
}

# Gain mapping (register value -> multiplier)
_GAIN_TO_MULT = {
    0x00: 1,
    0x01: 3,
    0x02: 6,
    0x03: 9,
    0x04: 18,
}
GAINS = [1,3,6,9,18]

class LTR390:
    def __init__(self, i2c, addr=0x53):
        self.i2c = i2c
        self.addr = addr
        self._gain_mult = 3          # current gain multiplier
        self._int_ms = 100           # current integration time (ms)
        # Verify sensor presence
        part_id = self._read_u8(_LTR390_PART_ID)
        if part_id != 0xB2:
            raise RuntimeError(f"Invalid LTR390 part ID: 0x{part_id:02X}")

    def _write_u8(self, reg, val):
        self.i2c.writeto_mem(self.addr, reg, bytes([val]))

    def _read_u8(self, reg):
        return self.i2c.readfrom_mem(self.addr, reg, 1)[0]

    def _read_20bit(self, reg_low):
        """Read 20‑bit data from three consecutive registers (low, mid, high)."""
        data = self.i2c.readfrom_mem(self.addr, reg_low, 3)
        return (data[2] << 16) | (data[1] << 8) | data[0]

    def set_gain(self, gain):
        """
        Set sensor gain.
        gain: 1, 3, 6, 9, or 18
        """
        for reg_val, mult in _GAIN_TO_MULT.items():
            if mult == gain:
                self._write_u8(_LTR390_GAIN, reg_val)
                self._gain_mult = gain
                return
        raise ValueError("Gain must be 1,3,6,9,18")

    def set_resolution(self, resolution_bits):
        """
        Set resolution (and integration time).
        resolution_bits: 16, 17, 18, 19, or 20
        """
        if resolution_bits == 20:
            reg_val = 0x00
            ms = 400
        elif resolution_bits == 19:
            reg_val = 0x01
            ms = 200
        elif resolution_bits == 18:
            reg_val = 0x02
            ms = 100
        elif resolution_bits == 17:
            reg_val = 0x03
            ms = 50
        elif resolution_bits == 16:
            reg_val = 0x04
            ms = 25
        else:
            raise ValueError("Resolution bits must be 16-20")
        # Measurement rate register: high nibble = resolution, low nibble = rate (use same for simplicity)
        self._write_u8(_LTR390_MEAS_RATE, (reg_val << 4) | reg_val)
        self._int_ms = ms

    def enable_uv(self, standby=False):
        """Enable UV sensor (and take it out of standby)."""
        ctrl = self._read_u8(_LTR390_MAIN_CTRL)
        ctrl &= ~0x01          # clear standby (0 = active)
        if standby:
            ctrl |= 0x01       # set standby if requested
        ctrl |= 0x04           # UVS enable (bit2)
        self._write_u8(_LTR390_MAIN_CTRL, ctrl)

    def disable(self):
        """Put sensor into standby (low power)."""
        ctrl = self._read_u8(_LTR390_MAIN_CTRL)
        ctrl |= 0x01          # standby bit
        self._write_u8(_LTR390_MAIN_CTRL, ctrl)

    def read_uv(self):
        """Return raw 20‑bit UV sensor reading."""
        return self._read_20bit(_LTR390_UVS_DATA0)

    def read_als(self):
        """Return raw 20‑bit ambient light reading."""
        return self._read_20bit(_LTR390_ALS_DATA0)

    def uv_index(self, raw=None):
        """
        Compute UV Index from raw reading, gain and integration time.
        Uses the typical sensitivity factor (2300 for Gain=3, 100ms).
        """
        if raw is None:
            raw = self.read_uv()
        # Sensitivity factor = baseline 2300 * (gain/3) * (int_time_ms/100)
        factor = 2300 * (self._gain_mult / 3.0) * (self._int_ms / 100.0)
        return raw / factor

# ----------------------------------------------------------------------
# Example usage (uncomment for testing)
# from machine import I2C, Pin
# i2c = I2C(0, scl=Pin(22), sda=Pin(21), freq=100000)
# sensor = LTR390(i2c)
# sensor.set_gain(3)
# sensor.set_resolution(18)          # 18-bit = 100ms integration
# sensor.enable_uv()
# import time
# time.sleep_ms(200)                 # first reading may be incomplete
# print("Raw UV:", sensor.read_uv())
# print("UV Index: {:.2f}".format(sensor.uv_index()))