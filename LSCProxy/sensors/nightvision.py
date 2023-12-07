# pylint: disable=C0114
from sensor import Sensor


class Nightvision(Sensor):
    """
    Night vision sensor class.
    """


    def toggle_switch(self, enable):
        """
        Toggles the switch based on the given enable state.

        Parameters:
            enable: Boolean value representing the desired state of the switch.

        Returns:
            None
        """

        if self._device_type == "switch":
            if enable:
                self.on()
            else:
                self.off()


    def on(self):
        """
        Enable night vision.
        """

        self._tutk.ioctrl_enable_nightvision()

    def off(self):
        """
        Disable night vision.
        """

        self._tutk.ioctrl_disable_nightvision()
