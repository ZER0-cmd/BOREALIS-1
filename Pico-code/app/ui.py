class Ui:
    def __init__(self, oled):
        self.oled = oled

    def _draw_image(self, path, x_offset=0, y_offset=0):
        with open(path, "r") as file:
            for p in file:
                p = p.strip().split(",")
                if len(p) != 3:
                    continue
                self.oled.pixel(int(p[0]) + x_offset,
                                int(p[1]) + y_offset,
                                int(p[2]))

    def show_boot(self, logo_path="pictures/logo.csv"):
        self.oled.fill(0)
        self._draw_image(logo_path)
        self.oled.show()

    def show_idle(self):
        self.oled.fill(0)
        self.oled.text("Borealis", 0, 0)
        self.oled.text("Waiting for sensor", 0, 20)
        self.oled.show()

    def show_sensor_connected(self, name):
        self.oled.fill(0)
        self.oled.text("Connected", 0, 0)
        self.oled.text(name, 0, 30)
        self.oled.show()

    def show_sensor_disconnected(self):
        self.oled.fill(0)
        self.oled.text("Disconnected", 0, 0)
        self.oled.text("waiting for sensor", 0, 15)
        self.oled.show()

    def show_unknown_sensor(self, adc_value):
        self.oled.fill(0)
        self.oled.text("Unknown", 0, 0)
        self.oled.text("ADC: %d" % adc_value, 0, 15)
        self.oled.show()

    def show_humidity_data(self, temp_c, humidity):
        self.oled.fill(0)
        self.oled.text("Humidity sensor", 0, 0)
        self.oled.text("Temp: %.1f C" % temp_c, 0, 15)
        self.oled.text("RH: %.1f %%" % humidity, 0, 25)
        self.oled.show()

    def show_pressure_data(self, temp_c, pressure_hpa):
        self.oled.fill(0)
        self.oled.text("Pressure sensor", 0, 0)
        self.oled.text("Temp: %.1f C" % temp_c, 0, 15)
        self.oled.text("P: %.1f hPa" % pressure_hpa, 0, 25)
        self.oled.show()

    def show_mpu6500_data(self, temp_c, ax, ay, az, gx, gy, gz):
        self.oled.fill(0)
        self.oled.text("MPU6500", 0, 0)
        self.oled.text("A X%.2f Y%.2f" % (ax, ay), 0, 15)
        self.oled.text("A Z%.2f g" % az, 0, 25)
        self.oled.text("G X%.0f Y%.0f" % (gx, gy), 0, 35)
        self.oled.text("G Z%.0f dps" % gz, 0, 45)
        self.oled.show()

    def show_error(self, msg):
        self.oled.fill(0)
        self.oled.text("ERROR", 0, 0)
        self.oled.text(str(msg)[:21], 0, 15)
        self.oled.show()
    
    