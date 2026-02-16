# app/safe_mode.py
import time

LEVEL_OK = 0
LEVEL_WARNING = 1
LEVEL_DEGRADED = 2
LEVEL_CRITICAL = 3
LEVEL_FATAL = 4

_LEVEL_NAMES = {
    LEVEL_OK: "OK",
    LEVEL_WARNING: "WARNING",
    LEVEL_DEGRADED: "DEGRADED",
    LEVEL_CRITICAL: "CRITICAL",
    LEVEL_FATAL: "FATAL",
}

def level_name(level: int) -> str:
    return _LEVEL_NAMES.get(level, "UNKNOWN")


class SafeModeManager:
    """
    Tracks the highest active safe-mode level + last error details.
    Also provides a non-blocking blink pattern scheduler.
    """
    def __init__(self, red_led):
        self.red_led = red_led
        self.level = LEVEL_OK

        self.last_error_where = ""
        self.last_error_type = ""
        self.last_error_msg = ""

        # blink scheduler
        self._blink_step = 0
        self._last_blink_ms = time.ticks_ms()
        self._blink_on = False

    def set_error(self, level: int, where: str, exc: Exception):
        # keep highest severity
        if level > self.level:
            self.level = level

        self.last_error_where = where
        self.last_error_type = exc.__class__.__name__
        # MicroPython exceptions sometimes don't have rich repr; str() is safest
        self.last_error_msg = str(exc)[:120]  # cap so we don't explode the OLED

    def clear_to_ok(self):
        self.level = LEVEL_OK
        self.last_error_where = ""
        self.last_error_type = ""
        self.last_error_msg = ""

    def tick_blink(self):
        """
        Call often (every loop). Blinks red LED according to current level.
        Non-blocking.
        """
        # Level 0: red off
        if self.level == LEVEL_OK:
            self.red_led.off()
            return

        now = time.ticks_ms()

        # Pattern: blink N times, pause, repeat (N = level)
        # timing values
        on_ms = 120
        off_ms = 120
        gap_ms = 700

        # We implement a simple step machine:
        # steps 0..(2*N-1) are blink on/off pairs, then a gap
        n = self.level  # 1..4
        total_steps = 2 * n

        # Decide current interval based on step
        interval = on_ms if self._blink_on else off_ms
        if self._blink_step >= total_steps:
            interval = gap_ms

        if time.ticks_diff(now, self._last_blink_ms) < interval:
            return  # not time yet

        self._last_blink_ms = now

        if self._blink_step < total_steps:
            # toggle LED each step
            self._blink_on = not self._blink_on
            if self._blink_on:
                self.red_led.on()
            else:
                self.red_led.off()
            self._blink_step += 1
        else:
            # gap finished, reset sequence
            self.red_led.off()
            self._blink_on = False
            self._blink_step = 0
