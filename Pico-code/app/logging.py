import uos
from drivers.sdcard import SDCard


def _mount(vfs, mount):
    """Mount vfs at mount point, unmounting first if already occupied."""
    try:
        uos.mount(vfs, mount)
    except OSError:
        uos.umount(mount)
        uos.mount(vfs, mount)


class loadfile():
    """
    Open an existing CSV file on the SD card in append mode.

    The first line of the file is read on init and parsed into a list of
    header strings so that write_row() can validate column counts correctly.
    """

    def __init__(self, sd, path: str, mount='/sd'):
        self.mount = mount
        _mount(uos.VfsFat(sd), self.mount)
        self.path = path

        # FIX: Read the header line with a dedicated handle that is closed
        # immediately after, then parse it into a list.  Previously the handle
        # was left open (resource leak) and the raw string was stored instead
        # of a list, causing len() to count characters instead of columns and
        # silently dropping every row written via write_row().
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
    """
    Create a new uniquely-named CSV file on the SD card.

    If <path>.csv already exists the filename is suffixed with an incrementing
    number: <path>1.csv, <path>2.csv, etc.
    """

    def __init__(self, sd, path: str, mount='/sd'):
        self.mount = mount
        self._headers = None
        _mount(uos.VfsFat(sd), self.mount)

        # Strip any extension the caller may have included
        if '.' in path:
            path = '.'.join(path.split('.')[:-1])

        def file_exists(filepath):
            try:
                uos.stat(filepath)
                return True
            except OSError:
                return False

        # FIX: The original code used f-string nested quotes
        # (f"{path + '.csv'}") which is only valid in Python 3.12+ and raises
        # a SyntaxError on MicroPython.  Use plain string concatenation instead.
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
    """Format the SD card. Destructive — all data will be lost."""
    if sd is not None:
        uos.VfsFat.mkfs(sd)