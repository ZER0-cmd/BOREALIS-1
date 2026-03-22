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
    App().run()
except Exception as e:
    # FATAL boot failure:
    # stay here so the error can be inspected in REPL
    blink(20)
    while True:
        pass