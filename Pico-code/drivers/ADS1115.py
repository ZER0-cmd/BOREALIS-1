import time
from micropython import const

# Register Addresses
_CONVERSION = const(0x00)
_CONFIG     = const(0x01)

# Multiplexer settings for single-ended reads
_MUX_SINGLE = {
    0: 0x4000,  # AIN0
    1: 0x5000,  # AIN1
    2: 0x6000,  # AIN2
    3: 0x7000   # AIN3
}

# Programmable Gain Amplifier (PGA) mapping 
# 0: +/-6.144V, 1: +/-4.096V, 2: +/-2.048V, 3: +/-1.024V, 4: +/-0.512V, 5: +/-0.256V
_PGA = {
    0: 0x0000, 1: 0x0200, 2: 0x0400, 3: 0x0600, 4: 0x0800, 5: 0x0A00
}

# Max voltages for calculating actual voltage
_VOLTAGES = {0: 6.144, 1: 4.096, 2: 2.048, 3: 1.024, 4: 0.512, 5: 0.256}

class ADS1115:
    def __init__(self, i2c, address=0x48, gain=1):
        """
        Default I2C address is 0x48 (ADDR pin connected to GND).
        Default gain is 1 (+/- 4.096V). Do not exceed VDD + 0.3V on any pin.
        """
        self.i2c = i2c
        self.address = address
        self.gain = gain
        
    def _write_register(self, reg, value):
        self.i2c.writeto_mem(self.address, reg, value.to_bytes(2, 'big'))
        
    def _read_register(self, reg):
        data = self.i2c.readfrom_mem(self.address, reg, 2)
        return int.from_bytes(data, 'big')

    def read(self, channel):
        """Reads the raw 16-bit ADC value from the specified channel (0-3)."""
        if channel not in [0, 1, 2, 3]:
            raise ValueError("Channel must be 0, 1, 2, or 3")
            
        # Build the config register value
        # OS(15) = 1 (start single-shot)
        # MUX(14:12) = selected channel
        # PGA(11:9) = selected gain
        # MODE(8) = 1 (single-shot mode)
        # DR(7:5) = 100 (128 SPS) -> 0x0080
        # COMP(4:0) = 0x0003 (Disable comparator)
        config = 0x8000 | _MUX_SINGLE[channel] | _PGA[self.gain] | 0x0100 | 0x0080 | 0x0003
        
        self._write_register(_CONFIG, config)
        
        # Wait for conversion to complete (1/128 SPS is ~7.8ms, wait 10ms to be safe)
        time.sleep_ms(10)
        
        # Read conversion register
        result = self._read_register(_CONVERSION)
        
        # Convert 16-bit unsigned to signed 2's complement
        if result > 32767:
            result -= 65536
            
        return result

    def read_voltage(self, channel):
        """Reads the channel and returns the calculated voltage."""
        raw = self.read(channel)
        v_per_bit = _VOLTAGES[self.gain] / 32768
        return raw * v_per_bit