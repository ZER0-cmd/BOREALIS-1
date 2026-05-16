from machine import Pin
import config
import time
from drivers.rtc_ds1302 import DS1302

class Timekeeper:
    def __init__(self):
        self.start_ticks_ms = time.ticks_ms()
        self.rtc_ok = False
        self.start_epoch = None
        self.rtc = None
        try:
            self.rtc = DS1302(
                Pin(config.DS1302_CLK),
                Pin(config.DS1302_DAT),
                Pin(config.DS1302_CE),
            )
            dt = self.rtc.datetime()
            self.start_epoch = self._dt_to_epoch(dt)
            self.rtc_ok = True
        except Exception as e:
            print("RTC init failed:", e)

    @staticmethod
    def _dt_to_epoch(dt):
        year, month, day, weekday, hour, minute, sec, _ = dt
        return time.mktime((year, month, day, hour, minute, sec,
                            (weekday - 1) % 7, 0))

    def elapsed_s(self):
        ticks_now = time.ticks_ms()
        uptime_s = time.ticks_diff(ticks_now, self.start_ticks_ms) / 1000.0

        if self.rtc_ok:
            try:
                now_epoch = self._dt_to_epoch(self.rtc.datetime())
                rtc_elapsed = now_epoch - self.start_epoch
                if uptime_s > 10 and rtc_elapsed < 1.0:
                    self.rtc_ok = False
                    return uptime_s
                return rtc_elapsed
            except Exception as e:
                print("RTC read failed:", e)
                self.rtc_ok = False

        return int(uptime_s)
    
    def fdate(self):
        if self.rtc_ok:
            y, mo, d, w, h, m, s, _= self.rtc.datetime()
            return f'{y}/{mo:02d}/{d:02d}@{h:02d}:{m:02d}:{s:02d}'