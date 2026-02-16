# drivers/storage_sdcard.py
# SD card driver for SPI on MicroPython (block device for VfsFat)
import time

_CMD_TIMEOUT = 100
_R1_IDLE_STATE = 1
_R1_ILLEGAL_COMMAND = 4

_TOKEN_CMD25 = 0xFC
_TOKEN_STOP_TRAN = 0xFD
_TOKEN_DATA = 0xFE


class SDCard:
    def __init__(self, spi, cs, baudrate=1_000_000):
        self.spi = spi
        self.cs = cs
        self.cs.init(self.cs.OUT, value=1)
        self.baudrate = baudrate
        self.cdv = 512  # may become 1 for SDHC/SDXC
        self._init_card()

    def _init_spi(self, baudrate):
        self.spi.init(baudrate=baudrate, polarity=0, phase=0)

    def _select(self):
        self.cs(0)

    def _deselect(self):
        self.cs(1)

    def _wait_ready(self, timeout=500):
        start = time.ticks_ms()
        while True:
            if self.spi.read(1, 0xFF)[0] == 0xFF:
                return True
            if time.ticks_diff(time.ticks_ms(), start) >= timeout:
                return False

    def _cmd(self, cmd, arg, crc=0x95):
        self._deselect()
        self.spi.read(1, 0xFF)
        self._select()
        self._wait_ready()

        buf = bytearray(6)
        buf[0] = 0x40 | cmd
        buf[1] = (arg >> 24) & 0xFF
        buf[2] = (arg >> 16) & 0xFF
        buf[3] = (arg >> 8) & 0xFF
        buf[4] = arg & 0xFF
        buf[5] = crc
        self.spi.write(buf)

        for _ in range(_CMD_TIMEOUT):
            r = self.spi.read(1, 0xFF)[0]
            if not (r & 0x80):
                return r
        return -1

    def _cmd_nodata(self, cmd, arg):
        r = self._cmd(cmd, arg)
        self._deselect()
        return r

    def _init_card(self):
        # init at low speed
        self._init_spi(100_000)

        self._deselect()
        for _ in range(10):
            self.spi.write(b"\xFF")

        r = self._cmd(0, 0, 0x95)  # CMD0
        if r not in (_R1_IDLE_STATE, 0):
            raise OSError("no SD card (CMD0)")

        r = self._cmd(8, 0x1AA, 0x87)  # CMD8
        if not (r & _R1_ILLEGAL_COMMAND):
            self.spi.read(4, 0xFF)

        # ACMD41 init loop
        for _ in range(1000):
            self._cmd(55, 0, 0x65)                 # CMD55
            r = self._cmd(41, 0x40000000, 0x77)    # ACMD41
            if r == 0:
                break
            time.sleep_ms(1)
        else:
            raise OSError("timeout waiting for ACMD41")

        # CMD58 read OCR to detect SDHC
        r = self._cmd(58, 0, 0xFD)
        ocr = bytearray(4)
        if r == 0:
            self.spi.readinto(ocr, 0xFF)
            self.cdv = 1 if (ocr[0] & 0x40) else 512
        else:
            self.cdv = 512

        # If not SDHC, set block length
        if self.cdv == 512:
            r = self._cmd(16, 512, 0x15)  # CMD16
            if r != 0:
                raise OSError("CMD16 failed")

        # switch to normal speed
        self._init_spi(self.baudrate)

    def readblocks(self, block_num, buf):
        nblocks = len(buf) // 512
        addr = block_num * self.cdv

        if nblocks == 1:
            if self._cmd(17, addr, 0xFF) != 0:
                raise OSError("read error (CMD17)")
            self._readinto(buf)
        else:
            if self._cmd(18, addr, 0xFF) != 0:
                raise OSError("read error (CMD18)")
            offset = 0
            for _ in range(nblocks):
                self._readinto(memoryview(buf)[offset:offset + 512])
                offset += 512
            self._cmd_nodata(12, 0)  # CMD12 stop

    def writeblocks(self, block_num, buf):
        nblocks = len(buf) // 512
        addr = block_num * self.cdv

        if nblocks == 1:
            if self._cmd(24, addr, 0xFF) != 0:
                raise OSError("write error (CMD24)")
            self._write(memoryview(buf))
        else:
            if self._cmd(25, addr, 0xFF) != 0:
                raise OSError("write error (CMD25)")
            offset = 0
            for _ in range(nblocks):
                self._write_token(_TOKEN_CMD25)
                self._write(memoryview(buf)[offset:offset + 512])
                offset += 512
            self._write_token(_TOKEN_STOP_TRAN)

        self._deselect()
        self.spi.read(1, 0xFF)

    def ioctl(self, op, arg):
        # op=4: return number of blocks
        if op == 4:
            if self._cmd(9, 0, 0xFF) != 0:  # CMD9 read CSD
                return 0
            csd = bytearray(16)
            self._readinto(csd)
            self._deselect()

            if csd[0] >> 6 == 1:
                c_size = ((csd[7] & 0x3F) << 16) | (csd[8] << 8) | csd[9]
                nblocks = (c_size + 1) * 1024
            else:
                c_size = ((csd[6] & 0x03) << 10) | (csd[7] << 2) | (csd[8] >> 6)
                c_size_mult = ((csd[9] & 0x03) << 1) | (csd[10] >> 7)
                nblocks = (c_size + 1) * (2 ** (c_size_mult + 2))
            return nblocks

        return 0

    def _readinto(self, buf):
        start = time.ticks_ms()
        while True:
            tok = self.spi.read(1, 0xFF)[0]
            if tok == _TOKEN_DATA:
                break
            if time.ticks_diff(time.ticks_ms(), start) > 1000:
                raise OSError("timeout waiting for data token")

        mv = memoryview(buf)
        self.spi.readinto(mv, 0xFF)
        self.spi.read(2, 0xFF)  # discard CRC

    def _write(self, buf):
        self._write_token(_TOKEN_DATA)
        self.spi.write(buf)
        self.spi.write(b"\xFF\xFF")  # dummy CRC

        resp = self.spi.read(1, 0xFF)[0]
        if (resp & 0x1F) != 0x05:
            raise OSError("data rejected")

        if not self._wait_ready():
            raise OSError("timeout after write")

    def _write_token(self, token):
        self.spi.write(bytearray([token]))
