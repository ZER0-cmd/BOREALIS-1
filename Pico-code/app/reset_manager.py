import machine
import time


class ResetManager:
    def __init__(self, pin, active_high=True):
        self.pin = pin
        self.active_high = active_high

    def is_triggered(self):
        val = self.pin.value()
        return val == 1 if self.active_high else val == 0

    def perform_reset(self, sd_logger=None, mount_point="/sd"):
        print("RESET TRIGGERED")

        # First choice: use existing SD logger wipe() if available
        if sd_logger is not None:
            try:
                sd_logger.wipe()
            except Exception as e:
                print("SD logger wipe failed:", e)

        # Fallback: delete files manually from mount point
        else:
            try:
                import uos
                files = uos.listdir(mount_point)
                for f in files:
                    path = "{}/{}".format(mount_point, f)
                    try:
                        uos.remove(path)
                    except OSError:
                        # maybe a directory
                        try:
                            uos.rmdir(path)
                        except Exception:
                            pass
            except Exception as e:
                print("Fallback wipe failed:", e)

        # Unmount SD if possible
        try:
            import os
            os.umount(mount_point)
        except Exception:
            pass

        # Small delay before reset
        time.sleep(0.5)

        # Hard reset Pico
        machine.reset()