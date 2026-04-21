import machine
import time
from app import logging

class ResetManager:
    def __init__(self, pin1, pin2):
        self.pin1 = pin1
        self.pin2 = pin2

    def is_triggered(self):
        val1 = self.pin1.value()
        val2 = self.pin2.value()
        if val1 == 1 or val2 == 1:
            for i in range(10):
                time.sleep(0.2)
                if val1 != 1 and val2 != 1:
                    return False
            return True
        return False

    def perform_reset(self, sd ,wipe=False):
        print("RESET TRIGGERED")

        if wipe:
            try:
                logging.wipe(sd)
            except Exception as e:
                print('SD wipe failed:', e)

            # Small delay before reset
            time.sleep(0.5)

        # Hard reset Pico
        machine.reset()