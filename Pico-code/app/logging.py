import machine
import uos
from drivers.sdcard import SDCard

class SDlogger:
    def __init__(self, spi, cs, head, file='data.csv', mount='/sd'):
        self.sd = SDCard(spi, cs)
        self.mount = mount
        vfs = uos.VfsFat(self.sd)
        try:
            uos.mount(vfs, mount)
        except OSError:
            uos.umount(mount)
            uos.mount(vfs, mount)
        self._file = open(f'{self.mount}/{file}', 'a')
        headers = open(f'{self.mount}/{file}', 'r').readline()
        if not headers:
            self.write_headers(head)
        else:
            self._headers = headers.strip().split(',')
    
    def write_headers(self, headers):
        self._headers = headers
        self._file.write(','.join(headers))
        self._file.write('\n')
        self._file.flush()

    def write_row(self, data) -> None:
        if self._headers is None:
            self.write_headers(data)
        if len(data) != len(self._headers):
            return
        self._file.write(','.join(['{:.2f}'.format(d) for d in data]))
        self._file.write('\n')
        self._file.flush()

    def stop(self) -> None:
        if self._file:
            try:
                self._file.flush()
            except Exception:
                pass
            try:
                self._file.close()
            except Exception:
                pass
        self._file = None
        self._path = None
    
    def wipe(self):
        files = uos.listdir(self.mount)
        for file in files:
            uos.remove(f'{self.mount}/{file}')
    
    def ls(self, source=None):
        if source is None:
            source = self.mount
        return uos.listdir(source)