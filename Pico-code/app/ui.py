class Ui:
    def __init__(self, oled):
        self.oled = oled

    def _format_time(self, time_ms):
        total_seconds = time_ms // 1000
        hours = (total_seconds // 3600) % 24
        minutes = (total_seconds // 60) % 60
        seconds = total_seconds % 60
        return "{:02d}:{:02d}:{:02d}".format(hours, minutes, seconds)

    def _draw_image(self, path, x_offset=0, y_offset=0):
        with open(path, "r") as file:
            for p in file:
                p = p.strip().split(',')
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
        self.oled.text("OLED OK", 0, 16)
        self.oled.text("Waiting...", 0, 32)
        self.oled.show()

    def show_off(self, utc_iso):
        self.oled.fill(0)
        self.oled.text("Experiment OFF", 0, 0)
        self.oled.text(utc_iso[:10], 0, 16)
        self.oled.text(utc_iso[11:19] + "Z", 0, 26)
        self.oled.text("Switch the switch", 0, 44)
        self.oled.text("to turn ON", 0, 54)
        self.oled.show()

    def show_on(self, temp_c, rh, utc_iso):
        self.oled.fill(0)
        self.oled.text("Borealis-1", 0, 0)
        self.oled.text("T: %.1f C" % temp_c, 0, 16)
        self.oled.text("H: %.1f %%" % rh, 0, 26)
        self.oled.text(utc_iso[:10], 0, 38)
        self.oled.text(utc_iso[11:19] + "Z", 0, 48)
        self.oled.show()

    def show_data(self, time_ms, alt, sensor, data, unit):
        self.oled.fill(0)
        self.oled.text("Borealis-1", 0, 0)
        self.oled.text("Time: %s" % self._format_time(time_ms), 0, 15)
        self.oled.text("Altitude: %.3f" % alt, 0, 25)
        self.oled.text("%s: %.3f %s" % (sensor, data, unit), 0, 35)
        self.oled.show()

    def show_error(self, level, where, err_type, msg):
        self.oled.fill(0)
        self.oled.text("ERROR: %s" % str(level)[:10], 0, 0)
        self.oled.text(str(where)[:21], 0, 16)
        self.oled.text(str(err_type)[:21], 0, 28)
        self.oled.text(str(msg)[:21], 0, 40)
        self.oled.show()