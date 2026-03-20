class Ui:
    """
    OLED rendering logic only.
    """
    def __init__(self, oled):
        self.oled = oled

    def show_boot(self):
        self.oled.fill(0)
        self.oled.text("Borealis", 28, 28)
        self.oled.show()

    def show_idle(self):
        self.oled.fill(0)
        self.oled.text("I am Borealis", 0, 0)
        self.oled.text("I am Borealis", 0, 16)
        self.oled.text("I am Borealis", 0, 32)
        self.oled.show()

    def show_off(self, utc_iso: str):
        self.oled.fill(0)
        self.oled.text("Experiment OFF", 0, 0)
        self.oled.text(utc_iso[:10], 0, 16)
        self.oled.text(utc_iso[11:19] + "Z", 0, 26)
        self.oled.text("Switch the switch", 0, 44)
        self.oled.text("to turn ON", 0, 54)
        self.oled.show()

    def show_on(self, temp_c: float, rh: float, utc_iso: str):
        self.oled.fill(0)
        self.oled.text("Borealis-1", 0, 0)
        self.oled.text("T: %.1f C" % temp_c, 0, 16)
        self.oled.text("H: %.1f %%" % rh, 0, 26)
        self.oled.text(utc_iso[:10], 0, 38)
        self.oled.text(utc_iso[11:19] + "Z", 0, 48)
        self.oled.show()

    def show_error(self, level: str, where: str, err_type: str, msg: str):
        self.oled.fill(0)
        self.oled.text("ERROR: %s" % level[:10], 0, 0)
        self.oled.text(where[:21], 0, 16)
        self.oled.text(err_type[:21], 0, 28)
        self.oled.text(msg[:21], 0, 40)
        self.oled.show()

    # For use with oled_images in scripts. It produces a csv file that can be read through path
    def show_image(self, path):
        self.oled.fill(0)
        with open(path, 'r') as file:
            pixels = [tuple(a.split(',')) for a in file.read().split()]
            for pixel in pixels:
                self.oled.pixel(*pixel)
    
    def _format_time(self, time):
        ms = time % 1000
        s = int(time/1000) % 60
        m = int(time/60000) % 60
        h = int(time/3600000)
        return f'{h}h : {m}m : {s}.{ms}s'

    def show_data(self, time, alt, sensor:str, data, unit:str):
        self.oled.fill(0)
        self.oled.text('Borealis-1', 0, 0)
        self.oled.text(f'Time: {self._format_time(time)}', 0, 15)
        self.oled.text(f'Altitude: {'{:.3f}'.format(alt)}', 0, 25)
        self.oled.text(f'{sensor}: {'{:.3f}'.format(data)}unit', 0, 35)