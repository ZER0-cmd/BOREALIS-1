from machine import I2C
import time


class BMP390:
    CHIP_IDS = (0x50, 0x60)   # BMP388, BMP390

    REG_CHIP_ID = 0x00
    REG_STATUS = 0x03
    REG_PRESS_DATA = 0x04
    REG_TEMP_DATA = 0x07
    REG_PWR_CTRL = 0x1B
    REG_OSR = 0x1C
    REG_ODR = 0x1D
    REG_CONFIG = 0x1F
    REG_CMD = 0x7E
    REG_CALIB = 0x31

    def __init__(self, i2c: I2C, address=0x77):
        self.i2c = i2c
        self.address = address
        self._t_lin = 0.0

        chip_id = self._read_u8(self.REG_CHIP_ID)
        if chip_id not in self.CHIP_IDS:
            raise OSError(
                "BMP3xx not found at 0x{:02X} (chip id = 0x{:02X})".format(
                    self.address, chip_id
                )
            )

        self.chip_id = chip_id
        self.reset()
        self._read_calibration()
        self.configure()

    # ---------- low-level helpers ----------

    def _read(self, reg, nbytes):
        return self.i2c.readfrom_mem(self.address, reg, nbytes)

    def _write(self, reg, data):
        if isinstance(data, int):
            data = bytes([data])
        self.i2c.writeto_mem(self.address, reg, data)

    def _read_u8(self, reg):
        return self._read(reg, 1)[0]

    def _read_u16_le(self, reg):
        b = self._read(reg, 2)
        return b[0] | (b[1] << 8)

    def _read_s8_from_buf(self, buf, idx):
        v = buf[idx]
        return v - 256 if v > 127 else v

    def _read_u16_from_buf(self, buf, idx):
        return buf[idx] | (buf[idx + 1] << 8)

    def _read_s16_from_buf(self, buf, idx):
        v = buf[idx] | (buf[idx + 1] << 8)
        return v - 65536 if v > 32767 else v

    def _read_u24_le(self, reg):
        b = self._read(reg, 3)
        return b[0] | (b[1] << 8) | (b[2] << 16)

    # ---------- sensor setup ----------

    def reset(self):
        self._write(self.REG_CMD, 0xB6)
        time.sleep_ms(10)

    def _read_calibration(self):
        # 21 bytes from 0x31..0x45
        c = self._read(self.REG_CALIB, 21)

        par_t1 = self._read_u16_from_buf(c, 0)
        par_t2 = self._read_u16_from_buf(c, 2)
        par_t3 = self._read_s8_from_buf(c, 4)

        par_p1 = self._read_s16_from_buf(c, 5)
        par_p2 = self._read_s16_from_buf(c, 7)
        par_p3 = self._read_s8_from_buf(c, 9)
        par_p4 = self._read_s8_from_buf(c, 10)
        par_p5 = self._read_u16_from_buf(c, 11)
        par_p6 = self._read_u16_from_buf(c, 13)
        par_p7 = self._read_s8_from_buf(c, 15)
        par_p8 = self._read_s8_from_buf(c, 16)
        par_p9 = self._read_s16_from_buf(c, 17)
        par_p10 = self._read_s8_from_buf(c, 19)
        par_p11 = self._read_s8_from_buf(c, 20)

        # Bosch compensation scaling
        self.par_t1 = par_t1 * 2.0**8
        self.par_t2 = par_t2 / 2.0**30
        self.par_t3 = par_t3 / 2.0**48

        self.par_p1 = (par_p1 - 2.0**14) / 2.0**20
        self.par_p2 = (par_p2 - 2.0**14) / 2.0**29
        self.par_p3 = par_p3 / 2.0**32
        self.par_p4 = par_p4 / 2.0**37
        self.par_p5 = par_p5 * 2.0**3
        self.par_p6 = par_p6 / 2.0**6
        self.par_p7 = par_p7 / 2.0**8
        self.par_p8 = par_p8 / 2.0**15
        self.par_p9 = par_p9 / 2.0**48
        self.par_p10 = par_p10 / 2.0**48
        self.par_p11 = par_p11 / 2.0**65

    def configure(
        self,
        pressure_oversampling=3,     # x8
        temperature_oversampling=3,  # x8
        iir_filter=0,                # off
        odr=3                        # reasonable default
    ):
        if not (0 <= pressure_oversampling <= 5):
            raise ValueError("pressure_oversampling must be 0..5")
        if not (0 <= temperature_oversampling <= 5):
            raise ValueError("temperature_oversampling must be 0..5")
        if not (0 <= iir_filter <= 7):
            raise ValueError("iir_filter must be 0..7")
        if not (0 <= odr <= 17):
            raise ValueError("odr must be 0..17")

        # OSR register: bits [2:0] pressure, [5:3] temperature
        osr = (temperature_oversampling << 3) | pressure_oversampling
        self._write(self.REG_OSR, osr)

        # Output data rate
        self._write(self.REG_ODR, odr)

        # IIR filter
        self._write(self.REG_CONFIG, iir_filter & 0x07)

        # Enable pressure + temperature, normal mode
        # bits [1:0] = enable press/temp
        # bits [5:4] = normal mode = 0b11
        self._write(self.REG_PWR_CTRL, 0x33)

        time.sleep_ms(20)

    # ---------- measurement ----------

    def _compensate_temperature(self, raw_temp):
        partial_data1 = raw_temp - self.par_t1
        partial_data2 = partial_data1 * self.par_t2
        self._t_lin = partial_data2 + (partial_data1 * partial_data1) * self.par_t3
        return self._t_lin

    def _compensate_pressure(self, raw_press):
        t_lin = self._t_lin
        t_lin2 = t_lin * t_lin
        t_lin3 = t_lin2 * t_lin

        partial_out1 = (
            self.par_p5
            + self.par_p6 * t_lin
            + self.par_p7 * t_lin2
            + self.par_p8 * t_lin3
        )

        partial_out2 = raw_press * (
            self.par_p1
            + self.par_p2 * t_lin
            + self.par_p3 * t_lin2
            + self.par_p4 * t_lin3
        )

        partial_data1 = raw_press * raw_press
        partial_data2 = self.par_p9 + self.par_p10 * t_lin
        partial_data3 = partial_data1 * partial_data2
        partial_data4 = partial_data3 + (raw_press * raw_press * raw_press) * self.par_p11

        return partial_out1 + partial_out2 + partial_data4

    def read(self):
        raw_temp = self._read_u24_le(self.REG_TEMP_DATA)
        temperature = self._compensate_temperature(raw_temp)

        raw_press = self._read_u24_le(self.REG_PRESS_DATA)
        pressure = self._compensate_pressure(raw_press)

        return temperature, pressure

    @property
    def temperature(self):
        return self.read()[0]

    @property
    def pressure(self):
        return self.read()[1]

    def altitude(self, sea_level_pressure_hpa=1013.25):
        _, pressure_pa = self.read()
        pressure_hpa = pressure_pa / 100.0
        return 44330.0 * (1.0 - (pressure_hpa / sea_level_pressure_hpa) ** 0.1903)