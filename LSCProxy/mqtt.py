# pylint: disable=E0401, W0612, W0613, C0114
import os
import time
import json
import sys
from sensors.nightvision import Nightvision
from sensors.private import Private
from sensors.flip import Flip
import paho.mqtt.client as mqtt


class LscMqttClient():
    """
    MQTT Client Class.

    This class represents an MQTT client for LSC (Light, Sensor, Camera) devices.

    Attributes:
        _tutk: Instance of the Tutk class for handling camera-related functionalities.
        _username: MQTT broker username.
        _password: MQTT broker password.
        _hostname: MQTT broker hostname.
        _port: MQTT broker port.
        _sensors: Dictionary to store Sensor objects.
        _client: Paho MQTT client instance.

    Methods:
        __init__(self, tutk, username, password, hostname, port,
            ffmpeg_process): Initializes the LSC MQTT client.
        _on_connect(self, client, userdata, flags, rc): Callback function on MQTT connection.
        _on_message(self, client, userdata, msg): Callback function on MQTT message reception.
        _start(self): Starts the MQTT client loop and handles MQTT interactions.
    """

    def __init__(self, tutk, username, password, hostname, port, ffmpeg_process):
        self._sensors = {}

        self._tutk = tutk
        self._username = username
        self._password = password
        self._hostname = hostname
        self._port = port

        self._client = mqtt.Client("ha-client")
        self._client.on_connect = self._on_connect
        self._client.on_message = self._on_message
        self._client.username_pw_set(username=self._username, password=self._password)
        keepalive = 60
        self._client.connect(self._hostname, self._port, keepalive)

        # Add sensors here ###
        nightvision = Nightvision("Night vision",
                                  "switch", "mdi:light-flood-down", self._tutk, ffmpeg_process)
        private = Private("Private", "switch", "mdi:eye-off", self._tutk, ffmpeg_process)
        flip = Flip("Flip", "switch", "mdi:flip-vertical", self._tutk, ffmpeg_process)

        self._sensors[nightvision.command_topic] = nightvision
        self._sensors[private.command_topic] = private
        self._sensors[flip.command_topic] = flip

    def _on_connect(self, client, userdata, flags, rc):
        """
        Callback function on MQTT connection.

        Parameters:
            client: Paho MQTT client instance.
            userdata: User data.
            flags: Connection flags.
            rc: Connection result code.

        Returns:
            None
        """

        if rc == 0:
            print(f"Sucessfully connected to broker: {self._hostname} on port {self._port}")
            for sensor_command_topic, sensor_object in self._sensors.items():
                found_sensor = self._sensors[sensor_command_topic]
                self._client.subscribe(found_sensor.subscribe)

            amount = 3
            for i in range(amount):
                for sensor_command_topic, sensor in self._sensors.items():
                    self._client.publish(sensor.config_topic, json.dumps(sensor.config_payload))
                time.sleep(1)

            # Try to get the last state from sensors
            states_dir = "states"
            if not os.path.exists(states_dir):
                os.makedirs(states_dir)
            print("Retrieving last state from sensors")
            for sensor_command_topic, sensor in self._sensors.items():
                sensor.read_last_state()
        else:
            print("Cannot connect to broker. Exit application")
            sys.exit(1)

    def _on_message(self, client, userdata, msg):
        """
        Callback function on MQTT message reception.

        Parameters:
            client: Paho MQTT client instance.
            userdata: User data.
            msg: MQTT message.

        Returns:
            None
        """

        topic = msg.topic
        payload = msg.payload.decode('utf-8')

        # If a topic is a command_topic from our sensors then handle the data
        if topic in self._sensors:
            found_sensor = self._sensors[topic]
            found_sensor.handle_data(payload)
            client.publish(found_sensor.state_topic, found_sensor.state_payload)

    def start(self):
        """
        Start the MQTT client loop and handle MQTT interactions.

        Returns:
            None
        """

        self._client.loop_start()

        while True:
            # Send  state to MQTT Server
            for command_topic, sensor_object in self._sensors.items():
                self._client.publish(sensor_object.state_topic, sensor_object.state_payload)
            time.sleep(1)
