from machine import I2C
import time

class MMC5603:
    # --- Registers ---
    XOUT0      = 0x00
    STATUS     = 0x18
    CTRL0      = 0x1B
    CTRL1      = 0x1C
    CTRL2      = 0x1D
    DEVICE_ID  = 0x39

    # --- Constants ---
    EXPECTED_ID = 0x10
    OFFSET      = 1 << 19  # 2^19 (524288) is the zero-field value for 20-bit data

    def __init__(self, i2c, address=0x30):
        """
        Initialize the MMC5603NJ sensor.
        :param i2c: A machine.I2C object.
        :param address: I2C address of the sensor (default is 0x30).
        """
        self.i2c = i2c
        self.address = address
        
        if not self._check_connection():
            raise RuntimeError("MMC5603NJ not found. Check wiring and I2C address.")
            
        # Optional: Software reset
        self._write_register(self.CTRL1, 0x80)
        time.sleep_ms(15)

    def _write_register(self, reg, value):
        self.i2c.writeto_mem(self.address, reg, bytes([value]))

    def _read_registers(self, reg, count):
        return self.i2c.readfrom_mem(self.address, reg, count)

    def _check_connection(self):
        try:
            dev_id = self._read_registers(self.DEVICE_ID, 1)[0]
            return dev_id == self.EXPECTED_ID
        except OSError:
            return False

    def read_raw(self):
        """
        Triggers a measurement and reads the 20-bit raw data.
        Returns: (x, y, z) tuple centered at 0.
        """
        # Trigger a single magnetic measurement: Set TM_M (bit 0) in CTRL0
        self._write_register(self.CTRL0, 0x01)

        # Poll the STATUS register until measurement is done (Bit 6 goes high)
        timeout = 50
        while timeout > 0:
            status = self._read_registers(self.STATUS, 1)[0]
            if status & 0x40:  # Meas_M_Done bit
                break
            time.sleep_ms(1)
            timeout -= 1

        if timeout == 0:
            raise RuntimeError("Sensor measurement timeout")

        # Read the 9 data registers starting at XOUT0
        data = self._read_registers(self.XOUT0, 9)

        # Assemble the 20-bit values
        # X: out0 (bits 19-12), out1 (bits 11-4), out2 (bits 3-0)
        x_raw = (data[0] << 12) | (data[1] << 4) | (data[6] >> 4)
        y_raw = (data[2] << 12) | (data[3] << 4) | (data[7] >> 4)
        z_raw = (data[4] << 12) | (data[5] << 4) | (data[8] >> 4)

        # Subtract the zero-field offset to get signed values
        x = x_raw - self.OFFSET
        y = y_raw - self.OFFSET
        z = z_raw - self.OFFSET

        return x, y, z