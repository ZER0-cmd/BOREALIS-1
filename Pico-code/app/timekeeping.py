class Timekeeper:
    """
    Small glue layer around an RTC driver to provide formatted timestamps.
    Expects an object with .datetime() that returns:
      (year, month, day, weekday, hour, minute, second, subseconds)
    """
    def __init__(self, rtc):
        self.rtc = rtc

    def utc_iso(self) -> str:
        y, m, d, wd, hh, mm, ss, sub = self.rtc.datetime()
        return "%04d-%02d-%02dT%02d:%02d:%02dZ" % (y, m, d, hh, mm, ss)
