import machine
import uos
from drivers.sdcard import SDCard

class loadfile():
    def __init__(self, sd, path:str, mount='/sd'):
        self.mount = mount
        vfs = uos.VfsFat(sd)
        try:
            uos.mount(vfs, self.mount)
        except OSError:
            uos.umount(self.mount)
            uos.mount(vfs, self.mount)
        self.path = path
        self._file = open(f'{self.mount}/{path}', 'a')
        self._headers = open(f'{self.mount}/{path}', 'r').readline()
    
    def write_headers(self, *headers):
        if type(headers[0]) != str:
            headers = headers[0]
        self._headers = headers
        self._file.write(','.join(headers) + '\n')

        self._file.flush()

    def write_row(self, *data) -> None:
        if type(data[0]) != str:
            data = data[0]
        if self._headers is None:
            self.write_headers(data)
        if len(data) != len(self._headers):
            return
        self._file.write(','.join(data) + '\n')
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
        self.path = None
    
    def wipe(self):
        files = uos.listdir(self.mount)
        for file in files:
            uos.remove(f'{self.mount}/{file}')
    
    def ls(self, source=None):
        if source is None:
            source = self.mount
        return uos.listdir(source)

class newfile(loadfile):
    def __init__(self, sd, path:str, mount='/sd'):
        self.mount = mount
        self._headers = None
        vfs = uos.VfsFat(sd)
        try:
            uos.mount(vfs, self.mount)
        except OSError:
            uos.umount(self.mount)
            uos.mount(vfs, self.mount)

        if '.' in path:
            path = path.split('.')[:-1]
        path = '.'.join(path)
        if uos.path.exists(f'{self.mount}/{path + 'csv'}'):
            n = 1
            while uos.path.exists(f'{self.mount}/{path + str(n) + 'csv'}'):
                n += 1
            path += str(n)
        path += '.csv'

        self._file = open(f'{self.mount}/{path}', 'w')
        self.path = path