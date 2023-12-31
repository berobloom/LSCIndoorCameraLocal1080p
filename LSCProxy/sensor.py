"""
Sensor Class.
"""


class Sensor:
    """
    Sensor Class.

    This class represents a sensor for LSC (Light, Sensor, Camera) devices.

    Attributes:
        _tutk: Instance of the Tutk class for handling camera-related functionalities.
        _device_type: Type of the device (e.g., switch).
        _friendly_name: User-friendly name of the sensor.
        _ffmpeg_process: Instance of the FFMPEG class.
        _safe_name: Sanitized and lowercased name of the sensor.
        _topic: MQTT topic associated with the sensor.
        _subscribe: MQTT topic used for subscribing to sensor commands.
        _config_topic: MQTT topic for sending sensor configuration to Home Assistant.
        _state_topic: MQTT topic for sending the state of the sensor to Home Assistant.
        _state_payload: Current state of the sensor.
        _command_topic: MQTT topic for receiving commands from Home Assistant.
        _config_payload: Payload containing sensor configuration for Home Assistant.
        _payload_dict: Dictionary mapping payload values to boolean states.

    Methods:
        __init__(self, name, device_type, icon, on_behavior, off_behavior, tutk,
            sensor_dict, ffmpeg_process):
            Initializes the Sensor object.
        handle_data(self, payload): Handles incoming
            commands from Home Assistant specific to switches.
        toggle_switch(self, enable): Toggles the switch based on the given enable state.
        save_state(self): Saves the current state of the sensor to a file.
        read_last_state(self): Reads the last saved state of the sensor from a file.

    Properties:
        command_topic: Getter for the command topic.
        topic: Getter for the topic.
        subscribe: Getter for the subscribe topic.
        config_topic: Getter for the config topic.
        config_payload: Getter for the config payload.
        state_topic: Getter for the state topic.
        state_payload: Getter for the state payload.
    """

    def __init__(self, name, device_type, icon, tutk, ffmpeg_process):
        self._tutk = tutk
        self._device_type = device_type
        self._friendly_name = name
        self._ffmpeg_process = ffmpeg_process

        self._safe_name = name.replace(" ", "").lower()
        self._topic = f"homeassistant/{device_type}/{self._safe_name}"
        self._subscribe = f"{self._topic}/#"
        self._config_topic = f"{self._topic}/config"
        self._state_topic = f"{self._topic}/state"
        self._state_payload = "OFF"
        self._command_topic = f"{self._topic}/set"
        self._config_payload = {
            "name": f"{self._friendly_name}",
            "device_class": f"{device_type}",
            "state_topic": f"{self._state_topic}",
            "command_topic": f"{self._command_topic}",
            "icon": f"{icon}",
            "unique_id": f"{self._safe_name}{device_type}02LSC02",
            "device": {
                "identifiers": [
                    "02LSC02"
                ],
                "manufacturer": "LSC",
                "model": "LSC Smart Connect Indoor Camera",
                "name": "LSC Indoor Camera"
            }
        }
        if device_type == "switch":
            self._config_payload["state_off"] = "OFF"
            self._config_payload["state_on"] = "ON"
            self._payload_dict = {
                "ON": True,
                "OFF": False,
            }

    def handle_data(self, payload):
        """
        Handles incoming commands from Home Assistant specific to switches.

        Parameters:
            payload: Payload received from Home Assistant.

        Returns:
            None
        """

        if self._device_type == "switch":
            for key, value in self._payload_dict.items():
                if payload == key:
                    self._toggle_switch(value)
                    self._state_payload = payload
                    self.save_state()
                    break

    def _toggle_switch(self, enable):
        """
        Toggles the switch based on the given enable state.

        Parameters:
            enable: Boolean value representing the desired state of the switch.

        Returns:
            None
        """

        if self._device_type == "switch":
            if enable:
                # Define this as a method in the subclass
                pass
            else:
                # Define this as a method in the subclass
                pass

    def save_state(self):
        """
        Saves the current state of the sensor to a file.

        Returns:
            None
        """

        file = f"states/{self._safe_name}"

        try:
            f = open(file, "x", encoding="utf-8")
        except:
            pass

        f = open(file, "r", encoding="utf-8")

        contents = f.read()
        if contents != self._state_payload:
            f = open(file, "w", encoding="utf-8")
            f.write(self._state_payload)
            f.close()

    def read_last_state(self):
        """
        Reads the last saved state of the sensor from a file.

        Returns:
            None
        """

        file = f"states/{self._safe_name}"

        try:
            f = open(file, "x", encoding="utf-8")
        except:

            pass

        f = open(file, "r", encoding="utf-8")

        contents = f.read()
        if contents in self._payload_dict:
            if self._device_type == "switch":
                if contents == "ON":
                    self._toggle_switch(True)
                if contents == "OFF":
                    self._toggle_switch(False)
                self._state_payload = contents

    @property
    def command_topic(self):
        """
        Getter for the command topic.

        Returns:
            MQTT command topic.
        """

        return self._command_topic

    @property
    def topic(self):
        """
        Getter for the topic.

        Returns:
            MQTT topic.
        """

        return self._topic

    @property
    def subscribe(self):
        """
        Getter for the subscribe topic.

        Returns:
            MQTT subscribe topic.
        """

        return self._subscribe

    @property
    def config_topic(self):
        """
        Getter for the config topic.

        Returns:
            MQTT config topic.
        """

        return self._config_topic

    @property
    def config_payload(self):
        """
        Getter for the config payload.

        Returns:
            MQTT config payload.
        """

        return self._config_payload

    @property
    def state_topic(self):
        """
        Getter for the state topic.

        Returns:
            MQTT state topic.
        """

        return self._state_topic

    @property
    def state_payload(self):
        """
        Getter for the state payload.

        Returns:
            MQTT state payload.
        """

        return self._state_payload
