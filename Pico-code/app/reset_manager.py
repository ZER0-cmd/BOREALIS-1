import machine
import time
from app import logging

class ResetManager:
    def __init__(self, pin, active_high=True):
        self.pin = pin
        self.active_high = active_high

    def is_triggered(self):
        val = self.pin.value()
        return val == 1 if self.active_high else val == 0

    def perform_reset(self, mount_point="/sd"):
        print("RESET TRIGGERED")

        try:
            logging.wipe(mount=mount_point, unmount=True)
        except Exception as e:
            print('SD wipe failed:', e)

        # Small delay before reset
        time.sleep(0.5)

        # Hard reset Pico
        machine.reset()