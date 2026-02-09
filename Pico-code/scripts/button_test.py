import time
import config
from drivers.input_button import Button

btn = Button(
    pin_num=config.BUTTON_PIN,
    pull=config.BUTTON_PULL,
    active_level=config.BUTTON_ACTIVE_LEVEL,
    debounce_ms=config.BUTTON_DEBOUNCE_MS
)

while True:
    print("active:", btn.is_active(), "raw:", btn.read())
    time.sleep(0.1)
