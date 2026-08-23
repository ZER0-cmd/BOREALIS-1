import uos
from drivers.sdcard import SDCard


def _mount(vfs, mount):
    try:
        uos.mount(vfs, mount)
    except OSError:
        uos.umount(mount)
        uos.mount(vfs, mount)


class loadfile():
    def __init__(self, sd, path: str, mount='/sd'):
        self.mount = mount
        _mount(uos.VfsFat(sd), self.mount)
        self.path = path

        with open(self.mount + '/' + path, 'r') as f:
            first_line = f.readline().strip()
        self._headers = first_line.split(',') if first_line else None

        self._file = open(self.mount + '/' + path, 'a')

    def write_headers(self, *headers):
        if not isinstance(headers[0], str):
            headers = headers[0]
        self._headers = [str(h) for h in headers]
        self._file.write(','.join(self._headers) + '\n')
        self._file.flush()

    def write_row(self, *data, safety=False) -> None:
        if not isinstance(data[0], str):
            data = data[0]
        if self._headers is None:
            self._headers = data
            self.write_headers(data)
        if len(data) != len(self._headers) and safety:
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
    def __init__(self, sd, path: str, mount='/sd'):
        self.mount = mount
        self._headers = None
        _mount(uos.VfsFat(sd), self.mount)

        if '.' in path:
            path = '.'.join(path.split('.')[:-1])

        def file_exists(filepath):
            try:
                uos.stat(filepath)
                return True
            except OSError:
                return False

        csv_path = self.mount + '/' + path + '.csv'
        if file_exists(csv_path):
            n = 1
            while file_exists(self.mount + '/' + path + str(n) + '.csv'):
                n += 1
            path = path + str(n)
        path = path + '.csv'

        self._file = open(self.mount + '/' + path, 'w')
        self.path = path


def wipe(sd):
    if sd is not None:
        uos.VfsFat.mkfs(sd)
