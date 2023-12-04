# pylint: disable=E0401, W0612, W0613
import os
import time
import json
import sys
from sensor import Sensor
import paho.mqtt.client as mqtt


class LscMqttClient():

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

        Sensor("Night vision", "switch", "mdi:light-flood-down",
                tutk.ioctrl_enable_nightvision, tutk.ioctrl_disable_nightvision,
                self.tutk, self.sensors, ffmpeg_process)
        Sensor("Flip", "switch", "mdi:flip-vertical",
                ffmpeg_process.enable_flip, ffmpeg_process.disable_flip,
                self.tutk, self.sensors, ffmpeg_process)
        Sensor("Private", "switch", "mdi:eye-off",
                tutk.ioctrl_stop_camera, tutk.ioctrl_start_camera,
                self.tutk, self.sensors, ffmpeg_process)

    def on_connect(self, client, userdata, flags, rc):
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
        topic = msg.topic
        payload = msg.payload.decode('utf-8')

        # If a topic is a command_topic from our sensors then handle the data
        if topic in self.sensors:
            found_sensor = self.sensors[topic]
            found_sensor.handle_data(payload)
            client.publish(found_sensor.state_topic, found_sensor.state_payload)


    def start(self):
        self.client.loop_start()

        while True:
            # Send  state to MQTT Server
            for command_topic, sensor_object in self.sensors.items():
                self.client.publish(sensor_object.state_topic, sensor_object.state_payload)
            time.sleep(1)
