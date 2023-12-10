"""
Services Module.

This module defines classes related to handling subprocesses and encapsulating
the functionality of the RTSP server and FFMPEG process.

Classes:
    Process: Wrapper class for subprocess.Popen,
    providing consistent process execution and termination.
    RTSPServer: Encapsulates the functionality to start and stop the RTSP server.
    FFMPEG: Encapsulates the functionality to start, stop, and restart the FFMPEG process.

Attributes:
    AUDIO_FIFO_PATH: Path to the audio FIFO.
    VIDEO_FIFO_PATH: Path to the video FIFO.
    MEDIAMTX_PATH: Path to the mediamtx command.

Note:
    This module assumes the existence of the following global variables:
    - AUDIO_FIFO_PATH: Path to the audio FIFO.
    - VIDEO_FIFO_PATH: Path to the video FIFO.
    - MEDIAMTX_PATH: Path to the mediamtx command.
"""

import subprocess
import pathlib
import signal
import sys
import os
import threading

AUDIO_FIFO_PATH = pathlib.Path().absolute() / "fifos/audio_fifo"
VIDEO_FIFO_PATH = pathlib.Path().absolute() / "fifos/video_fifo"
MEDIAMTX_PATH = pathlib.Path().absolute() / "rtsp/mediamtx"


class Process():
    """
    Wrapper class for subprocess.Popen.

    This class is designed to wrap around subprocess.Popen to provide consistent
    handling of process execution and termination.

    Attributes:
        process_object: An instance of the subprocess.Popen object.
        pid: Process ID (PID) of the running process.

    Methods:
        __init__(self, process_object): Initializes the Process object with a subprocess object.
        start(self): Starts the subprocess.
        stop(self): Stops the subprocess by sending a SIGKILL signal.
    """

    def __init__(self, process_object):
        self.process_object = process_object
        self.pid = None

    def start(self):
        """
        Start the subprocess.

        Returns:
            int: Return code of the subprocess.
        """

        return_code = 0
        if self.process_object is not None:
            try:
                with subprocess.Popen(
                    self.process_object.command,
                    stdin=subprocess.DEVNULL,
                    stdout=sys.stdout,
                    stderr=sys.stderr,
                ) as result:
                    self.pid = result.pid

            except subprocess.CalledProcessError as e:
                print(f"{self.process_object.name} failed with error: {e}")
                sys.exit(1)
            except FileNotFoundError:
                print(f"{self.process_object.name} not found")
                sys.exit(1)
            return_code = result.returncode
        else:
            print("Cannot start process. No process object has been given")

        return return_code

    def stop(self):
        """
        Stop the subprocess.

        Returns:
            None
        """

        if self.pid is not None:
            os.kill(self.pid, signal.SIGKILL)


class RTSPServer():
    """
    RTSP Server Wrapper Class.

    This class encapsulates the functionality to start and stop the RTSP server
    using the mediamtx command.

    Attributes:
        name: Name of the RTSP server process.
        command: Command to start the RTSP server.
        process: Instance of the Process class for managing the RTSP server process.

    Methods:
        __init__(self): Initializes the RTSPServer object with default settings.
        start(self): Starts the RTSP server process.
        stop(self): Stops the RTSP server process.
    """

    def __init__(self):
        self.name = "mediamtx"
        self.command = [MEDIAMTX_PATH, "rtsp/mediamtx.yml"]
        self.process = Process(self)

    def start(self):
        """
        Start the RTSP server process.

        Returns:
            None
        """

        self.process.start()

    def stop(self):
        """
        Stop the RTSP server process.

        Returns:
            None
        """

        self.process.stop()


class FFMPEG():
    """
    FFMPEG Wrapper Class.

    This class encapsulates the functionality to start, stop, and restart the FFMPEG process.

    Attributes:
        name: Name of the FFMPEG process.
        command: Command to start the FFMPEG process.
        is_flipped: Flag indicating if video output is flipped.
        _process: Instance of the Process class for managing the FFMPEG process.

    Methods:
        __init__(self): Initializes the FFMPEG object with default settings.
        start(self): Starts the FFMPEG process.
        stop(self): Stops the FFMPEG process.
        restart(self): Restarts the FFMPEG process.
        enable_flip(self): Enables video flipping and restarts the FFMPEG process.
        disable_flip(self): Disables video flipping and restarts the FFMPEG process.
    """

    def _ffmpeg_command_builder(self, video_filter=None):
        command = [
            "ffmpeg", "-re", "-hide_banner",
            "-thread_queue_size", "4096", "-f", "s16le", "-ar", "8000", "-ac", "1", "-i",
            AUDIO_FIFO_PATH,
            "-thread_queue_size", "4096", "-f", "h264", "-i",
            VIDEO_FIFO_PATH,
        ]

        if video_filter is not None:
            command.extend(["-vf", video_filter])

        command.extend([
            "-c:a", "aac", "-b:a", "32000", "-c:v", "libx264", "-preset",
            "ultrafast", "-tune", "zerolatency", "-async", "1",
            "-f", "rtsp", "-rtsp_transport", "tcp", "rtsp://localhost:8554/stream"
        ])
        return command

    def __init__(self):
        self.name = "ffmpeg"
        self.command = self._ffmpeg_command_builder()
        self.is_flipped = False

        self._process = Process(self)

    def start(self):
        """
        Start the FFMPEG process.

        Returns:
            None
        """

        # Keep ffmpeg running for Flip and Private sensor
        while True:
            normal_exit = 255
            interrupt = -9

            return_code = self._process.start()

            if return_code == normal_exit or return_code == interrupt:
                break

    def stop(self):
        """
        Stop the FFMPEG process.

        Returns:
            None
        """

        self._process.stop()

    def restart(self):
        """
        Restart the FFMPEG process.

        Returns:
            None
        """

        print("Restarting ffmpeg...")

        if self._process.pid is not None:
            self.stop()
        new_ffmpeg_thread = threading.Thread(target=self.start)
        new_ffmpeg_thread.daemon = True
        new_ffmpeg_thread.start()

    def enable_flip(self):
        """
        Enable video flipping and restart the FFMPEG process.

        Returns:
            None
        """

        if not self.is_flipped:
            self.command = self._ffmpeg_command_builder("hflip,vflip")
            self.is_flipped = True
            self.restart()

    def disable_flip(self):
        """
        Disable video flipping and restart the FFMPEG process.

        Returns:
            None
        """

        if self.is_flipped:
            self.command = self.command = self._ffmpeg_command_builder()
            self.is_flipped = False
            self.restart()
