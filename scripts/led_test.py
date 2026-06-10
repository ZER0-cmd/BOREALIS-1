import time
import config
from drivers.output_led import LED

red = LED(config.RED_LED_PIN, active_high=config.LED_ACTIVE_HIGH)
green = LED(config.GREEN_LED_PIN, active_high=config.LED_ACTIVE_HIGH)

while True:
    red.toggle()
    green.toggle()
    time.sleep(0.3)
