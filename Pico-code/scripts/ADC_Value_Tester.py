from machine import ADC
import time

adc = ADC(28)

while True:
    value = adc.read_u16()  # 0–65535 (scaled)
    
    # Convert to voltage (assuming 3.3V reference)
    voltage = value * 3.3 / 65535
    
    print("ADC:", value, "Voltage:", voltage, "V")
    
    time.sleep(0.5)