class Ui:
    def __init__(self, oled):
        self.oled = oled

    def _format_time(self, time_ms):
        total_seconds = time_ms // 1000
        hours = (total_seconds // 3600) % 24
        minutes = (total_seconds // 60) % 60
        seconds = total_seconds % 60
        return "{:02d}:{:02d}:{:02d}".format(hours, minutes, seconds)

    def _draw_csv_logo_scaled(self, path, x_offset=0, y_offset=0, scale_div=2, threshold=0.5):
        """
        Reads logo CSV lines in the format:
        x,y,brightness

        Example:
        0,0,0.0
        0,1,0.87
        0,2,1.0

        brightness is treated as grayscale float from 0.0 to 1.0.
        We threshold it to monochrome for the OLED.

        scale_div=2 means:
        64x64 source -> 32x32 display
        """
        with open(path, "r") as file:
            for line in file:
                line = line.strip()
                if not line:
                    continue

                parts = line.split(",")
                if len(parts) != 3:
                    continue

                try:
                    src_x = int(parts[0])
                    src_y = int(parts[1])
                    brightness = float(parts[2])
                except ValueError:
                    continue

                # Downscale by skipping pixels
                if src_x % scale_div != 0 or src_y % scale_div != 0:
                    continue

                x = (src_x // scale_div) + x_offset
                y = (src_y // scale_div) + y_offset

                # Convert grayscale -> OLED mono pixel
                color = 1 if brightness >= threshold else 0

                if 0 <= x < 128 and 0 <= y < 64:
                    self.oled.pixel(x, y, color)

    def show_boot(self, logo_path="pictures/logo.csv"):
        self.oled.fill(0)

        try:
            # 64x64 logo scaled down to 32x32
            # centered horizontally: (128 - 32) // 2 = 48
            self._draw_csv_logo_scaled(
                logo_path,
                x_offset=48,
                y_offset=4,
                scale_div=2,
                threshold=0.5
            )
        except Exception:
            pass

        self.oled.text("Borealis", 24, 44)
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