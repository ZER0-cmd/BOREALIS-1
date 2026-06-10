from machine import ADC
import time

adc = ADC(28)

while True:
    value = adc.read_u16()  # 0–65535 (scaled)
    
    # Convert to voltage (assuming 3.3V reference)
    u = 0
    n = 10
    for i in range(n):
        voltage = value * 3.3 / 65535
        u += voltage/n
        time.sleep(0.5/n)
    
    print("ADC:", value, "Voltage:", voltage, "V")
    