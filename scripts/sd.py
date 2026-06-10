import config
from machine import Pin, SPI
import machine
import uos
from drivers.sdcard import SDCard

spi = SPI(config.SD_SPI_ID, config.SD_BAUDRATE, polarity=0, phase=0, sck=Pin(config.SD_SCK), mosi=Pin(config.SD_MOSI), miso=Pin(config.SD_MISO))
cs=Pin(config.SD_CS)
mount=config.SD_MOUNT_POINT

sd = SDCard(spi, cs)
vfs = uos.VfsFat(sd)
uos.umount(mount)
uos.mount(vfs, mount)
