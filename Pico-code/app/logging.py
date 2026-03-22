import machine
import uos
from drivers.sdcard import SDCard

class SDlogger:
    def __init__(self, spi, cs, file='data.csv', mount='/sd'):
        self.sd = SDCard(spi, cs)
        self.mount = mount
        vfs = uos.VfsFat(self.sd)
        try:
            uos.mount(vfs, mount)
        except OSError:
            uos.umount(mount)
            uos.mount(vfs, mount)
        self._file = open(f'{self.mount}/{file}', 'a')
        if headers:
            self.write_headers(headers)
        else:
            headers = open(f'{self.mount}/{file}', 'r').readline()
            self._headers = headers.strip().split(',') if headers else None
    
    def write_headers(self, headers):
        self._headers = headers
        for s in headers:
            self._file.write(str(s) + ',')
        self._file.write('\n')
        self._file.flush()

    def write_row(self, data:tuple) -> None:
        if self._headers is None:
            self.write_headers(data)
        if len(data) != len(self._headers):
            return
        for d in data:
            self._file.write('{:.2f}'.format(d) + ',')
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