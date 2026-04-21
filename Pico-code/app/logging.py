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
        if not isinstance(headers[0], str):
            headers = headers[0]
        self._headers = [str(h) for h in headers]
        self._file.write(','.join(self._headers) + '\n')

        self._file.flush()

    def write_row(self, *data) -> None:
        if not isinstance(data[0], str):
            data = data[0]
        if self._headers is None:
            self._headers = data
            self.write_headers(data)
        if len(data) != len(self._headers):
            return
        data = [str(d) for d in data]
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

        def file_exists(filepath):
            try:
                uos.stat(filepath)
                return True
            except OSError:
                return False
        
        if file_exists(f'{self.mount}/{path + '.csv'}'):
            n = 1
            while file_exists(f'{self.mount}/{path + str(n) + '.csv'}'):
                n += 1
            path += str(n)
        path += '.csv'

        self._file = open(f'{self.mount}/{path}', 'w')
        self.path = path
    
def wipe(mount='/sd', unmount=False):
    files = uos.listdir(mount)
    for file in files:
        uos.remove(f'{mount}/{file}')
    if unmount:
        uos.umount(mount)