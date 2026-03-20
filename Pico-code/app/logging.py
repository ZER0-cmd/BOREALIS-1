import uos as os


class SdLogger:
    """
    Handles SD mount + CSV file lifecycle.
    """
    def __init__(self, mount_point="/sd"):
        self.mount_point = mount_point
        self.sd_ok = False
        self._mounted = False
        self._file = None
        self._path = None
        self._headers = None

    def mount(self, sdcard_block_device) -> bool:
        """
        Mount the SD card block device using VfsFat.
        Returns True if mounted OK.
        """
        try:
            vfs = os.VfsFat(sdcard_block_device)
            os.mount(vfs, self.mount_point)
            self.sd_ok = True
            self._mounted = True
            return True
        except Exception:
            self.sd_ok = False
            self._mounted = False
            return False

    def start_new(self, start_utc_iso: str) -> str | None:
        """
        Create a new CSV file and open it for append.
        Returns path if created, else None.
        """
        if not self.sd_ok:
            return None

        # Example: 20251206T121200Z.csv (safe filename)
        fn_safe = start_utc_iso.replace("-", "").replace(":", "")
        path = "%s/%s.csv" % (self.mount_point, fn_safe)

        # Write header
        with open(path, "w") as f:
            f.write("utc_iso,temp_c,humidity_percent\n")

        self._file = open(path, "a")
        self._path = path
        return path
    
    def write_headers(self, headers):
        self._headers = headers
        for s in headers:
            self._file.write(s + ',')
        self._file.write('\n')
        self._file.flush()

    def write_row(self, data:tuple) -> None:
        if not self._file:
            return
        if self._headers is None:
            self.write_headers(data)
        if len(data) != len(self.headers):
            return
        self._file.write("%s,%.2f,%.2f\n" % data)
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

    @property
    def current_path(self):
        return self._path
