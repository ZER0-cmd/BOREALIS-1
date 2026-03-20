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