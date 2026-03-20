import time
from machine import Pin

onboard = Pin(25, Pin.OUT)

def blink(n, on=0.12, off=0.12):
    for _ in range(n):
        onboard.on()
        time.sleep(on)
        onboard.off()
        time.sleep(off)

blink(1)

try:
    from app.controller import App
    blink(2)
    App().run()
except Exception as e:
    # FATAL boot failure
    while True:
        blink(5, on=0.05, off=0.05)
        time.sleep(1)