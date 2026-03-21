from machine import Pin


class SdDetect:
    """
    microSD card detect input.

    Expected behavior:
    - pin HIGH = no card
    - pin LOW  = card inserted

    active_low=True means LOW => inserted
    """
    def __init__(self, pin_num, active_low=True):
        self.pin = Pin(pin_num, Pin.IN)
        self.active_low = active_low

    def raw(self):
        return self.pin.value()

    def is_inserted(self):
        value = self.pin.value()
        if self.active_low:
            return value == 0
        else:
            return value == 1