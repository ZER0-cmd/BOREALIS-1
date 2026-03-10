import time
import machine
import math


class MAX31865():
    
    def __init__(self,
                 spi,
                 cs,
                 ref_r=430,
                 r0=100.,
                 wire3=False
                 ):
        
        '''
        needs the initialzed SPI object, a CS pin
        ref_r is the reference resistor on the board (430ohms)
        r0 is the sensor resitance at 0C (100 for PT100)
        wire3: set to True only for 3-wire Pt100 connection
        '''
        self.spi = spi
        cs.init(mode=machine.Pin.OUT)
        cs.value(1)
        self.cs = cs
        self.RefR = ref_r
        self.r0 = r0
        
        # details : https://www.analog.com/media/en/technical-documentation/data-sheets/MAX31865.pdf
        config = 0b11000011
        if wire3 : config = config | (1<<4) # set bit 4 of (0-7)       
        buf = bytearray(2)
        buf[0] = 0x80 #configuration write addr
        buf[1] = config        
        self._write(buf)

    def convert_res(self,raw):
        'converts raw sensor values to resistance in Ohm'        
        return raw  / 0x8000 * self.RefR
    
    def convert_temp(self,raw):
        'converts raw sensor values to temperature in C'
        r = self.convert_res(raw)/self.r0 # measured resistance devided by 0C R (100 for Pt100)
        #  Callendar Van Dusen equation
        a = 3.9083e-3
        b = -5.77500e-7
        # (1-r) + a*T + b*T**2 = 0
        # T**2 + a/b*T + (1-r)/b = 0
        p2 = a/b/2
        q = (1-r)/b
        return -p2 - math.sqrt( p2**2 - q )        
                        
    def temperature(self):
        'reads the sensor and returns temperature in C'        
        return self.convert_temp(self.read_sensor())
    
    def resistance(self):
        'reads the sensor and returns resistance in ohms'
        return self.convert_res(self.read_sensor())
        
    def read_all(self):
        'reads the sensor and returns a tuple (temperature in C,resistance in Ohm)'
        raw = self.read_sensor()
        return self.convert_temp(raw),self.convert_res(raw)                

    def read_sensor(self):
        'returns the raw 15bit sensor data'
        _,_,MSB,LSB = self._read(0x00,4)
        fault = LSB & 0x01
        raw = ((MSB<<8) + LSB) >> 1                        
        return raw    

    def _read(self,adr,num_bytes):
        self.cs.value(0)
        #time.sleep_us(10)
        ret = self.spi.read(num_bytes,adr)        
        self.cs.value(1)
        return ret
    
    def _write(self,buf):
        self.cs.value(0)
        self.spi.write(buf)
        self.cs.value(1)
        
        
def main():    
    import machine
    import time
    # from MAX31865 import MAX31865
    '''
    for wiring the module with the esp32 check:
    https://medium.com/@epabrego/1-micropython-esp32-max31865-rtd-pt100-9e9c02e2b55d
    machine.SPI(2) mode means
    CLK - VSPI_CLK (GPIO18)
    SDO - VSPI_MISO (GPIO19)
    SDI - VSPI_MOSI (GPIO23)
    '''
    spi = machine.SPI(2, baudrate=400000, polarity=0, phase=1)
    cs = machine.Pin(5)

    max31865 = MAX31865(spi, cs)
    
    while True:
        T,R = max31865.read_all()
        print(f'T = {T:.6} C , R = {R:.6} Ω')
        time.sleep(0.3)
    
if __name__ == '__main__':
    main()
    