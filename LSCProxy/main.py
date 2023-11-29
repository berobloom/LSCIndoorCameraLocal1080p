"""
main.py

This script establishes a connection to an IPCAM (Internet Protocol Camera)
using the Tutk library, configures various AVIOCTRL (Audio and Video Input/Output Control)
commands to start streaming, and manages multiple threads for video and audio
reception, RTSP (Real-Time Streaming Protocol) server,
ffmpeg streaming, and periodic buffer cleanup.

The script uses the Tutk library for communication with the IPCAM,
and it relies on the following modules:
- services: FFMPEG (for streaming audio and video) and RTSPServer (for handling RTSP connections)
- utils: usleep (a utility function for microsecond sleep)
- tutk: Tutk (a custom module for Tutk library operations) and AVIOCTRL message classes

Globals:
- AUDIO_BUF_SIZE: Size of the audio buffer
- VIDEO_BUF_SIZE: Size of the video buffer

IOCTRL constants:
- IOTYPE_USER_IPCAM_SETGRAY_MODE_REQ: IOCTRL constant for setting nightvision
- IOTYPE_USER_IPCAM_SETSTREAMCTRL_REQ: IOCTRL constant for setting stream control
- IOTYPE_USER_IPCAM_START: IOCTRL constant for starting the camera
- IOTYPE_USER_IPCAM_AUDIOSTART: IOCTRL constant for starting audio

Error constants:
- AV_ER_DATA_NOREADY: Error constant for no available data to read
- AV_ER_LOSED_THIS_FRAME: Error constant for losing the current frame
- AV_ER_SESSION_CLOSE_BY_REMOTE: Error constant for session close by remote
- AV_ER_REMOTE_TIMEOUT_DISCONNECT: Error constant for remote timeout disconnect
- IOTC_ER_INVALID_SID: Error constant for invalid session ID

Other constants:
- AUDIO_FIFO_PATH: Path to the audio FIFO file
- VIDEO_FIFO_PATH: Path to the video FIFO file

Functions:
- ioctrl_disable_nightvision: Disable night vision through AVIOCTRL.
- ioctrl_enable_hd_quality: Enable HD quality through AVIOCTRL.
- ioctrl_start_camera: Start the camera through AVIOCTRL.
- ioctrl_start_audio: Start audio streaming through AVIOCTRL.
- start_ipcam_stream: Start the IPCAM streaming by configuring various AVIOCTRL commands.
- receive_audio: Receive and playback audio data from the IPCAM stream.
- receive_video: Receive and playback video data from the IPCAM stream.
- clean_buffers: Periodically clean video and audio buffers.
- thread_ConnectCCR: Thread to connect to the camera, start streaming, and manage various threads.

Usage:
    python main.py <UID>

    where <UID> is the unique identifier of the IPCAM.

Note: This script should be executed with the UID (Unique Identifier)
of the target IPCAM as a command-line argument.
"""
import time
import os
import sys
import threading
import pathlib
from services import (
    FFMPEG,
    RTSPServer
)
from utils import usleep
from tutk import Tutk
from tutk import (
    SMsgAVIoctrlSetVideoModeReq,
    SMsgAVIoctrlSetStreamCtrlReq,
    SMsgAVIoctrlAVStream)

# Globals
AUDIO_BUF_SIZE = 512
VIDEO_BUF_SIZE = 64000

# IOCTRL constants
IOTYPE_USER_IPCAM_SETGRAY_MODE_REQ = 0x5000
IOTYPE_USER_IPCAM_SETSTREAMCTRL_REQ = 0x0320
IOTYPE_USER_IPCAM_START = 0x01FF
IOTYPE_USER_IPCAM_AUDIOSTART = 0x0300

# Error constants
AV_ER_DATA_NOREADY = -20012
AV_ER_LOSED_THIS_FRAME = -20014
AV_ER_SESSION_CLOSE_BY_REMOTE = -20015
AV_ER_REMOTE_TIMEOUT_DISCONNECT = -20016

IOTC_ER_INVALID_SID = -14

# Other constants
FIFOS_DIR = pathlib.Path().absolute() / "fifos"
AUDIO_FIFO_PATH = FIFOS_DIR / "audio_fifo"
VIDEO_FIFO_PATH = FIFOS_DIR / "video_fifo"
AV_USERNAME = "admin"
AV_PASSWORD = "123456"


def ioctrl_disable_nightvision(tutk):
    """
    Disable night vision through AVIOCTRL.

    Args:
        tutk (Tutk): Tutk object representing the camera.

    Returns:
        bool: True if successful, False otherwise.
    """
    io_nightvision = SMsgAVIoctrlSetVideoModeReq()
    io_nightvision.channel = 1
    io_nightvision.mode = 1

    status = tutk.av_send_ioctrl(IOTYPE_USER_IPCAM_SETGRAY_MODE_REQ, io_nightvision)

    return status


def ioctrl_enable_hd_quality(tutk):
    """
    Enable HD quality through AVIOCTRL.

    Args:
        tutk (Tutk): Tutk object representing the camera.

    Returns:
        bool: True if successful, False otherwise.
    """
    io_quality = SMsgAVIoctrlSetStreamCtrlReq()
    io_quality.channel = 0
    io_quality.quality = 2

    status = tutk.av_send_ioctrl(IOTYPE_USER_IPCAM_SETSTREAMCTRL_REQ, io_quality)

    return status



def ioctrl_start_camera(tutk):
    """
    Start the camera through AVIOCTRL.

    Args:
        tutk (Tutk): Tutk object representing the camera.

    Returns:
        bool: True if successful, False otherwise.
    """
    io_camera = SMsgAVIoctrlAVStream()
    io_camera.channel = 1

    status = tutk.av_send_ioctrl(IOTYPE_USER_IPCAM_START, io_camera)

    return status


def ioctrl_start_audio(tutk):
    """
    Start audio streaming through AVIOCTRL.

    Args:
        tutk (Tutk): Tutk object representing the camera.

    Returns:
        bool: True if successful, False otherwise.
    """
    io_audio = SMsgAVIoctrlAVStream()
    io_audio.channel = 1

    status = tutk.av_send_ioctrl(IOTYPE_USER_IPCAM_AUDIOSTART, io_audio)

    return status


def start_ipcam_stream(tutk):
    """
    Start the IPCAM streaming by configuring various AVIOCTRL commands.

    Args:
        tutk (Tutk): Tutk object representing the camera.

    Returns:
        bool: True if successful, False otherwise.
    """
    if not ioctrl_disable_nightvision(tutk):
        print("Cannot start camera. Error while disabling nightvision")
        return False

    if not ioctrl_enable_hd_quality(tutk):
        print("Cannot start camera. Error while setting quality to HD")
        return False

    if not ioctrl_start_camera(tutk):
        print("Cannot start camera. Camera error")
        return False

    if not ioctrl_start_audio(tutk):
        print("Cannot start camera. Error while starting audio")
        return False

    return True


def receive_audio(tutk):
    """
    Receive and playback audio data from the IPCAM stream.

    Args:
        tutk (Tutk): Tutk object representing the camera.
    """
    buf = tutk.create_buf(AUDIO_BUF_SIZE)

    print("Start IPCAM audio stream...")

    audio_pipe_fd = os.open(AUDIO_FIFO_PATH, os.O_WRONLY)
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

        status = tutk.av_recv_audio_data(buf, AUDIO_BUF_SIZE)

        if status == AV_ER_SESSION_CLOSE_BY_REMOTE:
            print("[thread_ReceiveAudio] AV_ER_SESSION_CLOSE_BY_REMOTE")
            break
        if status == AV_ER_REMOTE_TIMEOUT_DISCONNECT:
            print("[thread_ReceiveAudio] AV_ER_REMOTE_TIMEOUT_DISCONNECT")
            break
        if status == IOTC_ER_INVALID_SID:
            print("[thread_ReceiveAudio] Session cant be used anymore")
            break
        if status == AV_ER_LOSED_THIS_FRAME:
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

    video_pipe_fd = os.open(VIDEO_FIFO_PATH, os.O_WRONLY)
    if video_pipe_fd == -1:
        print("Cannot open video_fifo file")
    else:
        print("OK open video_fifo file")

    buf = tutk.create_buf(VIDEO_BUF_SIZE)

    while True:
        status = tutk.av_recv_framedata2(buf, VIDEO_BUF_SIZE)

        if status == AV_ER_DATA_NOREADY:
            usleep(10000)
            continue
        if status == AV_ER_SESSION_CLOSE_BY_REMOTE:
            print("[thread_ReceiveVideo] AV_ER_SESSION_CLOSE_BY_REMOTE")
            break
        if status == AV_ER_REMOTE_TIMEOUT_DISCONNECT:
            print("[thread_ReceiveVideo] AV_ER_REMOTE_TIMEOUT_DISCONNECT")
            break
        if status == IOTC_ER_INVALID_SID:
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


def thread_connect_ccr(tutk):
    """
    Thread to connect to the camera, start streaming, and manage various threads.

    Args:
        tutk (Tutk): Tutk object representing the camera.
    """
    tutk.iotc_connect_by_uid_parallel()

    tutk.av_client_start2(AV_USERNAME, AV_PASSWORD)

    print("Client started")

    if not start_ipcam_stream(tutk):
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

        video_thread.join()
        audio_thread.join()

        ffmpeg.stop()
        rtsp_server.stop()


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: ./AVAPIs_Client.py UID")
        sys.exit(1)

    uid = sys.argv[1]

    FIFOS_DIR = pathlib.Path().absolute() / "fifos"

    if not FIFOS_DIR.exists():
        FIFOS_DIR.mkdir(parents=True, exist_ok=True)
        print(f"Directory '{FIFOS_DIR}' created.")

    if not AUDIO_FIFO_PATH.exists():
        os.mkfifo(AUDIO_FIFO_PATH)
        print(f"Audio FIFO '{AUDIO_FIFO_PATH}' created.")

    if not VIDEO_FIFO_PATH.exists():
        os.mkfifo(VIDEO_FIFO_PATH)
        print(f"Video FIFO '{VIDEO_FIFO_PATH}' created.")

    tutk_framework = Tutk(uid)

    tutk_framework.iotc_initialize2(0)
    tutk_framework.av_initialize(2)

    ### Connect to the camera ###########
    try:
        print("LSC Indoor Camera Proxy v1.0")
        thread_connect_ccr(tutk_framework)
    except KeyboardInterrupt:
        tutk_framework.graceful_shutdown = True
        print("You pressed Ctrl+C!")
        print("Gracefully shutting down")

    #####################################

    tutk_framework.av_client_exit()
    tutk_framework.av_client_stop()
    tutk_framework.iotc_session_close()
    tutk_framework.iotc_de_initialize()

    print("LSC Indoor Camera Proxy v1.0. Shutted down.")
