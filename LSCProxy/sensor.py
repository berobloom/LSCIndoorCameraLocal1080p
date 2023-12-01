# pylint: disable=W0702
class Sensor:
    """
    Represents a sensor device for interaction with Home Assistant via MQTT.

    Attributes:
    - _tutk: The TUTK instance associated with the sensor.
    - _device_type (str): The type of the sensor device.
    - _friendly_name (str): The user-friendly name of the sensor.
    - _safe_name (str): The sanitized and lowercased version of the sensor's name.
    - _topic (str): The MQTT topic associated with the sensor.
    - _subscribe (str): The MQTT topic used for subscribing to sensor commands.
    - _config_topic (str): The MQTT topic for sending sensor configuration to Home Assistant.
    - _state_topic (str): The MQTT topic for sending the state of the sensor to Home Assistant.
    - _state_payload (str): The current state of the sensor.
    - _command_topic (str): The MQTT topic for receiving commands from Home Assistant.
    - _config_payload (dict): The payload containing sensor configuration for Home Assistant.
    - _payload_dict (dict): A dictionary mapping payload values to their corresponding boolean representations.

    Methods:
    - __init__(self, name, device_type, icon, tutk, sensor_dict): Initializes the Sensor instance.
    - handle_data(self, payload): Handles incoming commands specific to switches from Home Assistant.
    - toggle_switch(self, enable): Toggles the switch based on the enable parameter.
    - save_state(self): Saves the current state of the sensor to a file.
    - read_last_state(self): Reads the last saved state from a file and updates the sensor's state accordingly.

    Properties:
    - friendly_name: Getter for the user-friendly name of the sensor.
    - safe_name: Getter for the sanitized and lowercased name of the sensor.
    - topic: Getter for the MQTT topic associated with the sensor.
    - subscribe: Getter for the MQTT topic used for subscribing to sensor commands.
    - config_topic: Getter for the MQTT topic for sending sensor configuration to Home Assistant.
    - config_payload: Getter for the payload containing sensor configuration for Home Assistant.
    - command_topic: Getter for the MQTT topic for receiving commands from Home Assistant.
    - state_topic: Getter for the MQTT topic for sending the state of the sensor to Home Assistant.
    - state_payload: Getter and setter for the current state of the sensor.
    """
    def __init__(self, name, device_type, icon, tutk, sensor_dict):
        self._tutk = tutk
        self._device_type = device_type
        self._friendly_name = name

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
            "device":{
                "identifiers": [
                "02LSC02"
                ],
                "manufacturer": "LSC",
                "model": "LSC Smart Connect Indoor Camera",
                "name":"LSC Indoor Camera"
            }
        }
        if device_type == "switch":
            self.config_payload["state_off"] = "OFF"
            self.config_payload["state_on"] = "ON"
            self._payload_dict = {
                "ON": True,
                "OFF": False,
            }
        sensor_dict[self.command_topic] = self


    # Handle incoming commands from home assistant specific for switches
    def handle_data(self, payload):
        """
        Handles incoming commands specific to switches from Home Assistant.

        Parameters:
        - payload (str): The payload received from Home Assistant.
        """
        if self._device_type == "switch":
            for key, value in self._payload_dict.items():
                if payload == key:
                    self.toggle_switch(value)
                    self._state_payload = payload
                    self.save_state()
                    break

    def toggle_switch(self, enable):
        """
        Toggles the switch based on the enable parameter.

        Parameters:
        - enable (bool): True to enable the switch, False to disable it.
        """
        if self._device_type == "switch":
            if self._safe_name == "nightvision":
                if enable:
                    self._tutk.ioctrl_enable_nightvision()
                else:
                    self._tutk.ioctrl_disable_nightvision()

    def save_state(self):
        """
        Saves the current state of the sensor to a file.
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
        Reads the last saved state from a file and updates the sensor's state accordingly.
        """
        file = f"states/{self._safe_name}"
        try:
            f = open(file, "x", encoding="utf-8")
        except:
            pass
        f = open(file, "r", encoding="utf-8")
        contents = f.read()
        if contents in self._payload_dict.keys():
            if self._device_type == "switch":
                if contents == "ON":
                    self.toggle_switch(True)
                if contents == "OFF":
                    self.toggle_switch(False)
                self._state_payload = contents


    @property
    def friendly_name(self):
        """
        Getter for the user-friendly name of the sensor.
        """
        return self._friendly_name

    @property
    def safe_name(self):
        """
        Getter for the sanitized and lowercased name of the sensor.
        """
        return self._safe_name

    @property
    def topic(self):
        """
        Getter for the MQTT topic associated with the sensor.
        """
        return self._topic

    @property
    def subscribe(self):
        """
        Getter for the MQTT topic used for subscribing to sensor commands.
        """
        return self._subscribe

    @property
    def config_topic(self):
        """
        Getter for the MQTT topic for sending sensor configuration to Home Assistant.
        """
        return self._config_topic

    @property
    def config_payload(self):
        """
        Getter for the payload containing sensor configuration for Home Assistant.
        """
        return self._config_payload

    @property
    def command_topic(self):
        """
        Getter for the MQTT topic for receiving commands from Home Assistant.
        """
        return self._command_topic

    @property
    def state_topic(self):
        """
        Getter for the MQTT topic for sending the state of the sensor to Home Assistant.
        """
        return self._state_topic

    @property
    def state_payload(self):
        """
        Getter for the current state of the sensor.
        """
        return self._state_payload

    @state_payload.setter
    def state_payload(self,new_payload):
        """
        Setter for the current state of the sensor.
        """
        self._state_payload = new_payload
