"""
LSC Indoor Camera Proxy v1.0

This script establishes a connection to an indoor camera using the TUTK
framework.
It handles the reception of audio
and video streams, manages the RTSP server, and interacts with other services
such as FFMPEG and MQTT. The script takes a unique identifier (UID)
for the camera as a command-line argument and reads configuration
settings from a "settings.yaml" file.

Usage:
    ./main.py UID

Functions:
    - receive_audio(tutk): Continuously receives audio data from the
      TUTK framework
      and writes it to the audio FIFO file.
    - receive_video(tutk): Continuously receives video data from the
       TUTK framework
      and writes it to the video FIFO file.
    - clean_buffers(tutk): Periodically cleans video and audio buffers in the
      TUTK framework.
    - thread_connect_ccr(tutk, mqtt_enabled, mqtt_username, mqtt_password,
      mqtt_hostname, mqtt_port, av_username, av_password):
        Connects to the camera, starts video and audio streams,
        initializes RTSP server, and manages related threads.

Main:
    - Reads configuration settings from "settings.yaml" file.
    - Creates FIFO files for audio and video streams.
    - Initializes TUTK framework and establishes a connection to the camera.
    - Enters the main loop to manage camera streams and associated threads.
    - Gracefully shuts down on KeyboardInterrupt, closing all connections and
      stopping threads.

Author:
    Berobloom

Version:
    1.0
"""
# pylint: disable=W0621, E0401
import time
import os
import sys
import threading
import pathlib
import yaml
from services import (
    FFMPEG,
    RTSPServer
)
from utils import usleep
from mqtt import LscMqttClient
from tutk import Tutk


def receive_audio(tutk):
    """
    Continuously receives audio data from the TUTK framework and writes it
    to the audio FIFO file.

    Args:
        tutk (Tutk): The TUTK framework instance.

    Returns:
        None
    """

    buf = tutk.create_buf(Tutk.settings["AUDIO_BUF_SIZE"])

    print("Start IPCAM audio stream...")
    fifo_file = pathlib.Path().absolute() / Tutk.settings["AUDIO_FIFO_PATH"]
    audio_pipe_fd = os.open(fifo_file, os.O_WRONLY)
    if audio_pipe_fd == -1:
        print("Cannot open audio_fifo file")
    else:
        print("OK open audio_fifo file")

    while True:
        status = tutk.av_check_audio_buf()
        if status < 0:
            break
        if status < 50:
            usleep(10000)
            continue

        status = tutk.av_recv_audio_data(buf, Tutk.settings["AUDIO_BUF_SIZE"])

        if status == Tutk.error_constants["AV_ER_SESSION_CLOSE_BY_REMOTE"]:
            print("[thread_ReceiveAudio] AV_ER_SESSION_CLOSE_BY_REMOTE")
            break
        if status == Tutk.error_constants["AV_ER_REMOTE_TIMEOUT_DISCONNECT"]:
            print("[thread_ReceiveAudio] AV_ER_REMOTE_TIMEOUT_DISCONNECT")
            break
        if status == Tutk.error_constants["IOTC_ER_INVALID_SID"]:
            print("[thread_ReceiveAudio] Session cant be used anymore")
            break
        if status == Tutk.error_constants["AV_ER_LOSED_THIS_FRAME"]:
            continue

        if tutk.graceful_shutdown:
            break

        # Audio Playback
        try:
            status = os.write(audio_pipe_fd, buf)
            if status < 0:
                print(f"audio_playback::write , ret=[{status}]")
        except BrokenPipeError:
            usleep(10000)
            continue

    # Close unused pipe ends
    os.close(audio_pipe_fd)
    print("[receive_audio] thread exit")


def receive_video(tutk):
    """
    Continuously receives video data from the TUTK framework and writes it to
    the video FIFO file.

    Args:
        tutk (Tutk): The TUTK framework instance.

    Returns:
        None
    """

    print("Start IPCAM video stream...")

    fifo_file = pathlib.Path().absolute() / Tutk.settings["VIDEO_FIFO_PATH"]
    video_pipe_fd = os.open(fifo_file, os.O_WRONLY)
    if video_pipe_fd == -1:
        print("Cannot open video_fifo file")
    else:
        print("OK open video_fifo file")

    buf = tutk.create_buf(Tutk.settings["VIDEO_BUF_SIZE"])

    while True:
        status = tutk.av_recv_framedata2(buf, Tutk.settings["VIDEO_BUF_SIZE"])

        if status == Tutk.error_constants["AV_ER_DATA_NOREADY"]:
            usleep(10000)
            continue
        if status == Tutk.error_constants["AV_ER_SESSION_CLOSE_BY_REMOTE"]:
            print("[thread_ReceiveVideo] AV_ER_SESSION_CLOSE_BY_REMOTE")
            break
        if status == Tutk.error_constants["AV_ER_REMOTE_TIMEOUT_DISCONNECT"]:
            print("[thread_ReceiveVideo] AV_ER_REMOTE_TIMEOUT_DISCONNECT")
            break
        if status == Tutk.error_constants["IOTC_ER_INVALID_SID"]:
            print("[thread_ReceiveVideo] Session can't be used anymore")
            break

        if tutk.graceful_shutdown:
            break

        try:
            # Video Playback
            status = os.write(video_pipe_fd, buf)
            if status < 0:
                print(f"video_playback::write , ret=[{status}]")
        except BrokenPipeError:
            os.close(video_pipe_fd)
            # make this line shorter
            fifo_file = pathlib.Path().absolute() / Tutk.settings["VIDEO_FIFO_PATH"]
            video_pipe_fd = os.open(fifo_file, os.O_WRONLY)
            if video_pipe_fd == -1:
                print("Cannot open video_fifo file")
            else:
                print("OK open video_fifo file")
            usleep(10000)
            continue

    # Close unused pipe ends
    os.close(video_pipe_fd)
    print("[receive_video] thread exit")


def clean_buffers(tutk):
    """
    Periodically cleans video and audio buffers in the TUTK framework.

    Args:
        tutk (Tutk): The TUTK framework instance.

    Returns:
        None
    """

    while True:
        time.sleep(5)
        tutk.clean_video_buf()
        time.sleep(5)
        tutk.clean_audio_buf()


def thread_connect_ccr(tutk, mqtt_enabled, mqtt_username,
                       mqtt_password, mqtt_hostname, mqtt_port, av_username, av_password):
    """
    Connects to the camera, starts video and audio streams,
    initializes RTSP server, initializes MQTT client.

    Args:
        tutk (Tutk): The TUTK framework instance.
        mqtt_enabled (bool): Flag indicating whether MQTT is enabled.
        mqtt_username (str): MQTT username.
        mqtt_password (str): MQTT password.
        mqtt_hostname (str): MQTT broker hostname.
        mqtt_port (int): MQTT broker port.
        av_username (str): TUTK AV server username.
        av_password (str): TUTK AV server password.

    Returns:
        None
    """

    tutk.iotc_connect_by_uid_parallel()

    tutk.av_client_start2(av_username, av_password)

    print("Client started")

    if not tutk.start_ipcam_stream():
        sys.exit(1)
    else:
        print("IOCTRL commands send successfully")

        print("Starting RTSP Server...")
        rtsp_server = RTSPServer()
        rtsp_thread = threading.Thread(target=rtsp_server.start)
        rtsp_thread.daemon = True
        rtsp_thread.start()
        time.sleep(2)

        print("Starting video stream...")
        video_thread = threading.Thread(target=receive_video, args=(tutk,))
        video_thread.start()

        print("Starting audio stream...")
        audio_thread = threading.Thread(target=receive_audio, args=(tutk,))
        audio_thread.start()
        time.sleep(1)

        cleanup_buffers_thread = threading.Thread(target=clean_buffers, args=(tutk,))
        cleanup_buffers_thread.daemon = True
        cleanup_buffers_thread.start()

        print("Starting ffmpeg...")
        ffmpeg = FFMPEG()
        ffmpeg_thread = threading.Thread(target=ffmpeg.start)
        ffmpeg_thread.daemon = True
        ffmpeg_thread.start()

        if mqtt_enabled:
            print("Starting MQTT...")

            lsc_mqtt_client = LscMqttClient(tutk, mqtt_username, mqtt_password,
                                            mqtt_hostname, mqtt_port, ffmpeg)
            lsc_mqtt_client_thread = threading.Thread(target=lsc_mqtt_client.start)
            lsc_mqtt_client_thread.daemon = True
            lsc_mqtt_client_thread.start()

        video_thread.join()
        audio_thread.join()

        rtsp_server.stop()
        ffmpeg.stop()


def print_ascii_title():
    # pylint: disable=W1401
    """
    Prints the ASCII title.
    """
    title = """
  _     ____   ____ ____
 | |   / ___| / ___|  _ \ _ __ _____  ___   _
 | |   \___ \| |   | |_) | '__/ _ \ \/ / | | |
 | |___ ___) | |___|  __/| | | (_) >  <| |_| |
 |_____|____/ \____|_|   |_|  \___/_/\_\\__, |
                                        |___/
    """
    print(title)


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: ./main.py UID")
        sys.exit(1)

    uid = sys.argv[1]

    settings_yaml_file = pathlib.Path().absolute() / "settings.yaml"
    try:
        with open(settings_yaml_file, 'r', encoding='utf-8') as file:
            data = yaml.safe_load(file)

        mqtt_enabled = data['homeassistant_credentials']['enabled']
        if mqtt_enabled:
            mqtt_username = data['homeassistant_credentials']['mqtt_username']
            mqtt_password = data['homeassistant_credentials']['mqtt_password']
            mqtt_hostname = data['homeassistant_credentials']['mqtt_hostname']
            mqtt_port = data['homeassistant_credentials']['mqtt_port']

        av_username = data['tutk_credentials']['av_username']
        av_password = data['tutk_credentials']['av_password']

    except KeyError as e:
        print(f"Error: Required key not found: {e}")
        sys.exit(1)

    fifos_dir = pathlib.Path().absolute() / Tutk.settings["FIFOS_DIR"]
    audio_fifo_file = pathlib.Path().absolute() / Tutk.settings["AUDIO_FIFO_PATH"]
    video_fifo_file = pathlib.Path().absolute() / Tutk.settings["VIDEO_FIFO_PATH"]

    if not fifos_dir.exists():
        fifos_dir.mkdir(parents=True, exist_ok=True)
        print(f"Directory '{fifos_dir}' created.")

    if not audio_fifo_file.exists():
        os.mkfifo(audio_fifo_file)
        print(f"Audio FIFO '{audio_fifo_file}' created.")

    if not video_fifo_file.exists():
        os.mkfifo(video_fifo_file)
        print(f"Video FIFO '{video_fifo_file}' created.")

    tutk_framework = Tutk(uid)

    tutk_framework.iotc_initialize2(0)
    tutk_framework.av_initialize(2)

    # Connect to the camera
    try:
        print_ascii_title()
        print("-Version: 1.0-\n")

        thread_connect_ccr(tutk_framework, mqtt_enabled, mqtt_username,
                           mqtt_password, mqtt_hostname, mqtt_port, av_username, av_password)
    except KeyboardInterrupt:
        tutk_framework.graceful_shutdown = True
        print("You pressed Ctrl+C!")
        print("Gracefully shutting down")

    tutk_framework.av_client_stop()
    tutk_framework.iotc_session_close()
    tutk_framework.iotc_de_initialize()

    print("\nLSC Indoor Camera Proxy v1.0. Shutted down.")
