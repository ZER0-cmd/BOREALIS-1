def guard(method):
    def wrapped(self, *args, **kwargs):
        try:
            return method(self, *args, **kwargs)
        except Exception:
            self.oled = None
            return None
    return wrapped

def applyguard(cls):
    for attr_name in dir(cls):
        attr = getattr(cls, attr_name)
        if attr_name.startswith('_'):
            continue
        if callable(attr):
            setattr(cls, attr_name, guard(attr))
    return cls

@applyguard
class Ui:
    def __init__(self, oled):
        self.oled = oled

    def text_center(self, text, y):
        # Each character is ~8 pixels wide in MicroPython OLED font
        char_width = 8
        text_width = len(text) * char_width

        # OLED width from display
        screen_width = self.oled.width

        # Calculate centered X position
        x = max(0, (screen_width - text_width) // 2)

        self.oled.text(text, x, y)

    def draw_image(self, img, x_offset=0, y_offset=0, center=False):
        xdim, ydim = img.DIM
        data = img.PIXELS

        x_center = ((self.oled.width - xdim) // 2) if center else 0
        # y_center = ((self.oled.height - ydim) // 2) if center else 0
        
        for i in range(0, len(data), 2):
            x = data[i]   + x_offset + x_center
            y = data[i+1] + y_offset
            if 0 <= x < self.oled.width and 0 <= y < self.oled.height:
                self.oled.pixel(x, y, 1)

    def show_boot(self):
        from pictures import logo
        self.oled.fill(0)
        self.draw_image(logo, center=True)

    def show_sensor_connected(self, name):
        self.oled.fill(0)
        try:
            img = __import__("pictures." + name.replace(' ', ''), None, None, [name])
            self.draw_image(img, center=True)
        except ImportError:
            pass
        self.text_center(name, 55)    

    def show_sensor_disconnected(self):
        self.oled.fill(0)
        self.text_center("Disconnected:", 0)
        self.oled.text("waiting for sensor", 0, 15)   

    def show_unknown_sensor(self, adc_value):
        self.oled.fill(0)
        self.text_center("Unknown", 0)
        self.oled.text("ADC: %d" % adc_value, 0, 15)
        
    def show_humidity_data(self, humidity):
        self.oled.fill(0)
        self.text_center("Humidity sensor", 0)
        # self.oled.text("Temp: %.1f C" % temp_c, 0, 15)
        self.oled.text("RH: %.1f %%" % humidity, 0, 15)

    def show_pressure_data(self, pressure_hpa):
        self.oled.fill(0)
        self.text_center("Pressure sensor", 0)
        # self.oled.text("Temp: %.1f C" % temp_c, 0, 15)
        self.oled.text("P: %.1f hPa" % pressure_hpa, 0, 15)

    def show_mpu6500_data(self, ax, ay, az, gx, gy, gz):
        self.oled.fill(0)
        self.text_center("MPU6500", 0)
        self.oled.text("A X%.2E Y%.2E" % (ax, ay), 0, 15)
        self.oled.text("A Z%.2E g" % az, 0, 25)
        self.oled.text("G X%.0f Y%.0f" % (gx, gy), 0, 35)
        self.oled.text("G Z%.0f dps" % gz, 0, 45)

    def show_temp_data(self, temp):
        self.oled.fill(0)
        self.text_center("Temperature", 0)
        self.oled.text("Temp: %.2E C" % temp, 0, 15)
    
    def show_solar_data(self, v):
        self.oled.fill(0)
        self.text_center("Solar", 0)
        self.oled.text("Voltage: %.2E V" % v, 0, 15)
    
    def show_light_data(self, uv):
        self.oled.fill(0)
        self.text_center("UV", 0)
        self.oled.text("UV-index: %.2E" % uv, 0, 15)
    
    def show_gas_data(self, v):
        self.oled.fill(0)
        self.text_center("MQ-Sensor", 0)
        self.oled.text("Presence: %.2E" % v, 0, 15)
        
    def show_magnet_data(self,x,y,z):
        self.oled.fill(0)
        self.text_center("Magnetic strength", 0)
        self.oled.text("X%d Y%d Z%d" % (x,y,z), 0, 15)

    def show_error(self, msg):
        self.oled.fill(0)
        self.text_center("ERROR", 0)
        self.oled.text(str(msg)[:21], 0, 15)

    def show_resetting(self):
        self.oled.fill(0)
        self.text_center("RESETTING...", 28)
        self.oled.show()

    def show_calibrating(self, sensor):
        self.oled.fill(0)
        self.text_center(str(sensor), 0)
        self.oled.text('CALIBRATING', 0, 15)
        self.oled.text('Do not move', 0, 25)
    
    def show_calibration_abort(self, msg):
        self.oled.fill(0)
        self.text_center('CALIBRATON', 0)
        self.text_center('FAILED', 10)
        self.text_center(str(msg), 25)
    
    def show_newfile(self, path):
        self.oled.fill(0)
        self.oled.text('Created new file', 0, 15)
        self.text_center(str(path), 25)
    
    def clear(self):
        self.oled.fill(0)
        self.oled.show()

    def text(self, *args):
        self.oled.text(*args)
    def show(self):
        self.oled.show()