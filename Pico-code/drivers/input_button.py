from machine import Pin
import time


class Button:
    """
    Debounced digital input.

    pull: "up" or "down"
    active_level: 0 or 1 (the level that means "active")
    """
    def __init__(self, pin_num, pull="down", active_level=1, debounce_ms=30):
        if pull == "up":
            p = Pin.PULL_UP
        else:
            p = Pin.PULL_DOWN

        self.pin = Pin(pin_num, Pin.IN, p)
        self.active_level = 1 if active_level else 0
        self.debounce_ms = debounce_ms

        self._stable = self.pin.value()
        self._last_read = self._stable
        self._last_change_ms = time.ticks_ms()

    def read(self) -> int:
        raw = self.pin.value()
        now = time.ticks_ms()

        if raw != self._last_read:
            self._last_read = raw
            self._last_change_ms = now

        # If stable for debounce window, accept
        if time.ticks_diff(now, self._last_change_ms) >= self.debounce_ms:
            self._stable = self._last_read

        return self._stable

    def is_active(self) -> bool:
        return self.read() == self.active_level
