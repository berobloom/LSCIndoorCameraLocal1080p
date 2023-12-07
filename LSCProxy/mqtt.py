# pylint: disable=E0401, W0612, W0613
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
        tutk: Instance of the Tutk class for handling camera-related functionalities.
        username: MQTT broker username.
        password: MQTT broker password.
        hostname: MQTT broker hostname.
        port: MQTT broker port.
        sensors: Dictionary to store Sensor objects.
        client: Paho MQTT client instance.

    Methods:
        __init__(self, tutk, username, password, hostname, port, ffmpeg_process): Initializes the LSC MQTT client.
        on_connect(self, client, userdata, flags, rc): Callback function on MQTT connection.
        on_message(self, client, userdata, msg): Callback function on MQTT message reception.
        start(self): Starts the MQTT client loop and handles MQTT interactions.
    """

    def __init__(self, tutk, username, password, hostname, port, ffmpeg_process):
        self.sensors = {}

        self.tutk = tutk
        self.username = username
        self.password = password
        self.hostname = hostname
        self.port = port

        self.client = mqtt.Client("ha-client")
        self.client.on_connect = self.on_connect
        self.client.on_message = self.on_message
        self.client.username_pw_set(username=self.username, password=self.password)
        keepalive = 60
        self.client.connect(self.hostname, self.port, keepalive)

        ### Add sensors here ###
        nightvision = Nightvision("Night vision", "switch", "mdi:light-flood-down", self.tutk, ffmpeg_process)
        private = Private("Private", "switch", "mdi:eye-off", self.tutk, ffmpeg_process)
        flip = Flip("Flip", "switch", "mdi:flip-vertical", self.tutk, ffmpeg_process)

        self.sensors[nightvision.command_topic] = nightvision
        self.sensors[private.command_topic] = private
        self.sensors[flip.command_topic] = flip
        ### Add sensors here ###

    def on_connect(self, client, userdata, flags, rc):
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
            print(f"Sucessfully connected to broker: {self.hostname} on port {self.port}")
            for sensor_command_topic, sensor_object in self.sensors.items():
                found_sensor = self.sensors[sensor_command_topic]
                self.client.subscribe(found_sensor.subscribe)

            amount = 3
            for i in range(amount):
                for sensor_command_topic, sensor in self.sensors.items():
                    self.client.publish(sensor.config_topic, json.dumps(sensor.config_payload))
                time.sleep(1)

            # Try to get the last state from sensors
            states_dir = "states"
            if not os.path.exists(states_dir):
                os.makedirs(states_dir)
            print("Retrieving last state from sensors")
            for sensor_command_topic, sensor in self.sensors.items():
                sensor.read_last_state()
        else:
            print("Cannot connect to broker. Exit application")
            sys.exit(1)


    def on_message(self, client, userdata, msg):
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
        if topic in self.sensors:
            found_sensor = self.sensors[topic]
            found_sensor.handle_data(payload)
            client.publish(found_sensor.state_topic, found_sensor.state_payload)


    def start(self):
        """
        Start the MQTT client loop and handle MQTT interactions.

        Returns:
            None
        """

        self.client.loop_start()

        while True:
            # Send  state to MQTT Server
            for command_topic, sensor_object in self.sensors.items():
                self.client.publish(sensor_object.state_topic, sensor_object.state_payload)
            time.sleep(1)
