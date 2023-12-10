# pylint: disable=C0114, E0401
from sensor import Sensor


class Flip(Sensor):
    """
    Flip sensor class.
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
        Enable video flipping and restart the FFMPEG process.
        """

        if not self._ffmpeg_process.is_flipped:
            self._ffmpeg_process.enable_flip()
            self._ffmpeg_process.restart()

    def off(self):
        """
        Disable video flipping and restart the FFMPEG process.
        """

        if self._ffmpeg_process.is_flipped:
            self._ffmpeg_process.disable_flip()
            self._ffmpeg_process.restart()
