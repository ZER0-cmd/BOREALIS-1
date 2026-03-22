from machine import I2C
import time


class MPU6500:
    # Registers
    REG_WHO_AM_I      = 0x75
    REG_PWR_MGMT_1    = 0x6B
    REG_SMPLRT_DIV    = 0x19
    REG_CONFIG        = 0x1A
    REG_GYRO_CONFIG   = 0x1B
    REG_ACCEL_CONFIG  = 0x1C
    REG_ACCEL_CONFIG2 = 0x1D
    REG_INT_PIN_CFG   = 0x37
    REG_ACCEL_XOUT_H  = 0x3B
    REG_TEMP_OUT_H    = 0x41
    REG_GYRO_XOUT_H   = 0x43

    WHO_AM_I_EXPECTED = 0x70  # MPU6500

    def __init__(self, i2c: I2C, address=0x68):
        self.i2c = i2c
        self.address = address

        # default scale settings
        self.accel_scale = 16384.0  # ±2g
        self.gyro_scale = 131.0     # ±250 dps

        who = self._read_u8(self.REG_WHO_AM_I)
        if who != self.WHO_AM_I_EXPECTED:
            raise OSError(
                "MPU6500 not found at 0x{:02X} (WHO_AM_I = 0x{:02X})".format(
                    self.address, who
                )
            )

        self._init_sensor()

    def _write_u8(self, reg, val):
        self.i2c.writeto_mem(self.address, reg, bytes([val]))

    def _read_u8(self, reg):
        return self.i2c.readfrom_mem(self.address, reg, 1)[0]

    def _read_bytes(self, reg, n):
        return self.i2c.readfrom_mem(self.address, reg, n)

    def _to_int16(self, msb, lsb):
        value = (msb << 8) | lsb
        if value & 0x8000:
            value -= 65536
        return value

    def _init_sensor(self):
        # Wake up device
        self._write_u8(self.REG_PWR_MGMT_1, 0x00)
        time.sleep_ms(100)

        # Sample rate divider
        self._write_u8(self.REG_SMPLRT_DIV, 0x00)

        # DLPF
        self._write_u8(self.REG_CONFIG, 0x03)

        # Gyro ±250 dps
        self.set_gyro_range(250)

        # Accel ±2g
        self.set_accel_range(2)

        # Accel DLPF
        self._write_u8(self.REG_ACCEL_CONFIG2, 0x03)

        time.sleep_ms(20)

    def set_accel_range(self, g_range):
        if g_range == 2:
            self._write_u8(self.REG_ACCEL_CONFIG, 0x00)
            self.accel_scale = 16384.0
        elif g_range == 4:
            self._write_u8(self.REG_ACCEL_CONFIG, 0x08)
            self.accel_scale = 8192.0
        elif g_range == 8:
            self._write_u8(self.REG_ACCEL_CONFIG, 0x10)
            self.accel_scale = 4096.0
        elif g_range == 16:
            self._write_u8(self.REG_ACCEL_CONFIG, 0x18)
            self.accel_scale = 2048.0
        else:
            raise ValueError("accel range must be 2, 4, 8, or 16")

    def set_gyro_range(self, dps_range):
        if dps_range == 250:
            self._write_u8(self.REG_GYRO_CONFIG, 0x00)
            self.gyro_scale = 131.0
        elif dps_range == 500:
            self._write_u8(self.REG_GYRO_CONFIG, 0x08)
            self.gyro_scale = 65.5
        elif dps_range == 1000:
            self._write_u8(self.REG_GYRO_CONFIG, 0x10)
            self.gyro_scale = 32.8
        elif dps_range == 2000:
            self._write_u8(self.REG_GYRO_CONFIG, 0x18)
            self.gyro_scale = 16.4
        else:
            raise ValueError("gyro range must be 250, 500, 1000, or 2000")

    def read_accel_raw(self):
        data = self._read_bytes(self.REG_ACCEL_XOUT_H, 6)
        ax = self._to_int16(data[0], data[1])
        ay = self._to_int16(data[2], data[3])
        az = self._to_int16(data[4], data[5])
        return ax, ay, az

    def read_temp_raw(self):
        data = self._read_bytes(self.REG_TEMP_OUT_H, 2)
        return self._to_int16(data[0], data[1])

    def read_gyro_raw(self):
        data = self._read_bytes(self.REG_GYRO_XOUT_H, 6)
        gx = self._to_int16(data[0], data[1])
        gy = self._to_int16(data[2], data[3])
        gz = self._to_int16(data[4], data[5])
        return gx, gy, gz

    def read_accel(self):
        ax, ay, az = self.read_accel_raw()
        return ax / self.accel_scale, ay / self.accel_scale, az / self.accel_scale

    def read_gyro(self):
        gx, gy, gz = self.read_gyro_raw()
        return gx / self.gyro_scale, gy / self.gyro_scale, gz / self.gyro_scale

    def read_temperature(self):
        raw = self.read_temp_raw()
        # MPU6500 temperature conversion
        return (raw / 333.87) + 21.0

    def read_all(self):
        ax, ay, az = self.read_accel()
        gx, gy, gz = self.read_gyro()
        temp = self.read_temperature()
        return {
            "accel_g": (ax, ay, az),
            "gyro_dps": (gx, gy, gz),
            "temp_c": temp,
        }