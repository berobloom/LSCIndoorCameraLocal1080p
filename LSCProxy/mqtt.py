"""
LscMqttClient Module

This module defines the LscMqttClient class, representing a client
for interacting with an MQTT broker to manage sensors.
It includes callback functions for connecting to the MQTT broker and handling received messages.
"""
# pylint: disable=E0401, W0612, W0613
import os
import time
import json
import sys
from sensor import Sensor
import paho.mqtt.client as mqtt


class LscMqttClient():
    """
    Represents a client for interacting with an MQTT broker to manage sensors.

    Attributes:
    - tutk (str): The TUTK identifier.
    - username (str): The username for connecting to the MQTT broker.
    - password (str): The password for connecting to the MQTT broker.
    - hostname (str): The hostname or IP address of the MQTT broker.
    - port (int): The port number of the MQTT broker.

    Methods:
    - __init__(self, tutk, username, password, hostname, port): Initializes the LscMqttClient.
    - on_connect(self, client, userdata, flags, rc):
      Callback function when the client connects to the MQTT broker.
    - on_message(self, client, userdata, msg): Callback function
      when a message is received from the MQTT broker.
    - start(self): Starts the MQTT client and continuously sends sensor states to the MQTT server.
    """
    def __init__(self, tutk, username, password, hostname, port):
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
        self.client.connect(self.hostname, self.port, 60)

        Sensor("Night vision", "switch", "mdi:light-flood-down", self.tutk, self.sensors)


    def on_connect(self, client, userdata, flags, rc):
        """
        Callback function when the client connects to the MQTT broker.

        Parameters:
        - client: The MQTT client instance.
        - userdata: User data passed when the callback was set.
        - flags: Response flags from the broker.
        - rc (int): The result code returned by the broker.
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
        Callback function when a message is received from the MQTT broker.

        Parameters:
        - client: The MQTT client instance.
        - userdata: User data passed when the callback was set.
        - msg: The message received from the broker.
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
        Starts the MQTT client and continuously sends sensor states to the MQTT server.
        """
        self.client.loop_start()

        while True:
            # Send  state to MQTT Server
            for command_topic, sensor_object in self.sensors.items():
                self.client.publish(sensor_object.state_topic, sensor_object.state_payload)
            time.sleep(1)
