# pylint: disable=C0114, E0401
from sensor import Sensor


class Private(Sensor):
    """
    Private sensor class.
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
        Enable private.
        """

        self._tutk.ioctrl_stop_camera()


    def off(self):
        """
        Disable private.
        """

        self._tutk.ioctrl_start_camera()
