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

    def draw_image(self, path, x_offset=0, y_offset=0, center=False):
        with open(path, "r") as file:
            xdim = 0
            ydim = 0
            for p in file:
                p = p.strip().split(",")
                if len(p) != 3:
                    if len(p) == 2:
                        xdim = int(p[0])
                        ydim = int(p[1])
                    continue
                self.oled.pixel(int(p[0]) + x_offset + ((self.oled.width - xdim)//2 if center else 0),
                                int(p[1]) + y_offset,
                                int(p[2]))

    def show_boot(self, logo_path="pictures/logo.csv"):
        self.oled.fill(0)
        self.draw_image(logo_path)    

    def show_sensor_connected(self, name, kind):
        self.oled.fill(0)
        # self.text_center("Connected:", 0)
        try:
            self.draw_image(f'pictures/{kind}.csv',center=True)
        except OSError:
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
        
    def show_humidity_data(self, temp_c, humidity):
        self.oled.fill(0)
        self.text_center("Humidity sensor", 0)
        self.oled.text("Temp: %.1f C" % temp_c, 0, 15)
        self.oled.text("RH: %.1f %%" % humidity, 0, 25)

    def show_pressure_data(self, temp_c, pressure_hpa):
        self.oled.fill(0)
        self.text_center("Pressure sensor", 0)
        self.oled.text("Temp: %.1f C" % temp_c, 0, 15)
        self.oled.text("P: %.1f hPa" % pressure_hpa, 0, 25)

    def show_mpu6500_data(self, temp_c, ax, ay, az, gx, gy, gz):
        self.oled.fill(0)
        self.text_center("MPU6500", 0)
        self.oled.text("A X%.2f Y%.2f" % (ax, ay), 0, 15)
        self.oled.text("A Z%.2f g" % az, 0, 25)
        self.oled.text("G X%.0f Y%.0f" % (gx, gy), 0, 35)
        self.oled.text("G Z%.0f dps" % gz, 0, 45)

    def show_temp_data(self, temp):
        self.oled.fill(0)
        self.text_center("Temperature", 0)
        self.oled.text("Temp: %.2f C" % temp, 0, 15)
    
    def show_solar_data(self, v):
        self.oled.fill(0)
        self.text_center("Solar", 0)
        self.oled.text("Voltage: %.2f V" % v, 0, 15)

    def show_error(self, msg):
        self.oled.fill(0)
        self.text_center("ERROR", 0)
        self.oled.text(str(msg)[:21], 0, 15)

    def show_resetting(self):
        self.oled.fill(0)
        self.text_center("RESETTING...", 28)
        self.oled.show()