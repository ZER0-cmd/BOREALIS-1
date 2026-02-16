from machine import Pin
import time


class LED:
    def __init__(self, pin_no, active_high=True):
        self.pin = Pin(pin_no, Pin.OUT)
        self.active_high = active_high
        self.off()

    def on(self):
        self.pin.value(1 if self.active_high else 0)

    def off(self):
        self.pin.value(0 if self.active_high else 1)

    def toggle(self):
        self.pin.value(1 - self.pin.value())

    def blink(self, times=1, interval=0.2):
        for _ in range(times):
            self.on()
            time.sleep(interval)
            self.off()
            time.sleep(interval)
