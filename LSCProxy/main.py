"""
main.py

This script establishes a connection to an IPCAM, receives audio and video streams,
plays back the streams, and manages various threads for cleanup and additional services.

The script uses the Tutk library for IPCAM communication, FFMPEG for audio and video streaming,
RTSPServer for RTSP streaming, and LscMqttClient for MQTT communication.

Functions:
- receive_audio(tutk): Receive and playback audio data from the IPCAM stream.
- receive_video(tutk): Receive and playback video data from the IPCAM stream.
- clean_buffers(tutk): Periodically clean video and audio buffers.
- thread_connect_ccr(tutk, mqtt_enabled, mqtt_username, mqtt_password,
  mqtt_hostname, mqtt_port, av_username, av_password):
  Thread to connect to the camera, start streaming, and manage various threads.

Usage:
python main.py UID

The script reads configuration settings from the "settings.yaml" file, including MQTT credentials,
Tutk credentials, and FIFO paths. Make sure to provide the UID as a command-line argument.
"""
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
# pylint: disable=W0621


def receive_audio(tutk):
    """
    Receive and playback audio data from the IPCAM stream.

    Args:
        tutk (Tutk): Tutk object representing the camera.
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
        if status < 25:
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

        # Audio Playback
        status = os.write(audio_pipe_fd, buf)
        if status < 0:
            print(f"audio_playback::write , ret=[{status}]")

        if tutk.graceful_shutdown:
            break

    # Close unused pipe ends
    os.close(audio_pipe_fd)
    print("[receive_audio] thread exit")


def receive_video(tutk):
    """
    Receive and playback video data from the IPCAM stream.

    Args:
        tutk (Tutk): Tutk object representing the camera.
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

        # Video Playback
        status = os.write(video_pipe_fd, buf)
        if status < 0:
            print(f"video_playback::write , ret=[{status}]")

        if tutk.graceful_shutdown:
            break

    # Close unused pipe ends
    os.close(video_pipe_fd)
    print("[receive_video] thread exit")


def clean_buffers(tutk):
    """
    Periodically clean video and audio buffers.

    Args:
        tutk (Tutk): Tutk object representing the camera.
    """
    while True:
        time.sleep(5)
        tutk.clean_video_buf()
        time.sleep(30)
        tutk.clean_audio_buf()


def thread_connect_ccr(tutk, mqtt_enabled, mqtt_username,
                           mqtt_password, mqtt_hostname, mqtt_port, av_username, av_password):
    """
    Thread to connect to the camera, start streaming, and manage various threads.

    Args:
        tutk (Tutk): Tutk object representing the camera.
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
        stream_av_thread = threading.Thread(target=ffmpeg.start)
        stream_av_thread.daemon = True
        stream_av_thread.start()

        if mqtt_enabled:
            print("Starting MQTT...")
            lsc_mqtt_client = LscMqttClient(tutk, mqtt_username, mqtt_password,
                                                  mqtt_hostname, mqtt_port)
            lsc_mqtt_client_thread = threading.Thread(target=lsc_mqtt_client.start)
            lsc_mqtt_client_thread.daemon = True
            lsc_mqtt_client_thread.start()

        video_thread.join()
        audio_thread.join()

        ffmpeg.stop()
        rtsp_server.stop()


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: ./AVAPIs_Client.py UID")
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
        sys.exit(1)  # Exit with an error code

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

    ### Connect to the camera ###########
    try:
        print("LSC Indoor Camera Proxy v1.0")
        thread_connect_ccr(tutk_framework, mqtt_enabled, mqtt_username,
                           mqtt_password, mqtt_hostname, mqtt_port, av_username, av_password)
    except KeyboardInterrupt:
        tutk_framework.graceful_shutdown = True
        print("You pressed Ctrl+C!")
        print("Gracefully shutting down")

    #####################################

    tutk_framework.av_client_stop()
    tutk_framework.iotc_session_close()
    tutk_framework.iotc_de_initialize()

    print("\nLSC Indoor Camera Proxy v1.0. Shutted down.")
