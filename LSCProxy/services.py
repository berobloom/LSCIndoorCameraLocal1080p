"""
services.py

This script manages external processes, specifically an RTSP server (mediamtx)
and an FFMPEG process. It provides classes for Process, RTSPServer,
and FFMPEG, allowing the start and stop of these processes.

Classes:
- Process: A class for managing external processes.
    Attributes:
        - process_object (ProcessObject): An object representing the process to be managed.
        - pid (int): The process ID (PID) of the running process.
    Methods:
        - start(): Start the specified process.
        - stop(): Stop the running process.

- RTSPServer: A class for managing an RTSP server process.
    Methods:
        - start(): Start the RTSP server process.
        - stop(): Stop the RTSP server process.
        - get_pid(): Get the PID of the RTSP server process.

- FFMPEG: A class for managing an FFMPEG process.
    Methods:
        - start(): Start the FFMPEG process.
        - stop(): Stop the FFMPEG process.
        - get_pid(): Get the PID of the FFMPEG process.

Attributes:
- AUDIO_FIFO_PATH: Path to the audio FIFO (First In, First Out) file.
- VIDEO_FIFO_PATH: Path to the video FIFO file.
- MEDIAMTX_PATH: Path to the mediamtx executable.

Usage:
    Modify the attributes and command parameters as needed for the specific external processes.
    Run this script to start and stop the RTSP server and FFMPEG processes.

Note: Ensure that the required external binaries (mediamtx, ffmpeg)
are available in the system PATH.
"""
import subprocess
import pathlib
import signal
import sys
import os

AUDIO_FIFO_PATH = pathlib.Path().absolute() / "fifos/audio_fifo"
VIDEO_FIFO_PATH = pathlib.Path().absolute() / "fifos/video_fifo"
MEDIAMTX_PATH = pathlib.Path().absolute() / "rtsp/mediamtx"


class Process():
    """
    A class for managing external processes.

    Attributes:
    - process_object (ProcessObject): An object representing the process to be managed.
    - pid (int): The process ID (PID) of the running process.

    Methods:
    - start(): Start the specified process.
    - stop(): Stop the running process.
    """
    def __init__(self, process_object):
        self.process_object = process_object
        self.pid = None

    def start(self):
        """
        Start the specified process.

        Raises:
        - subprocess.CalledProcessError: If the process execution returns a non-zero exit code.
        - FileNotFoundError: If the specified executable is not found.
        - Exception: For other unexpected errors during process start.
        """
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
        else:
            print("Cannot start process. No process object has been given")

    def stop(self):
        """
        Stop the running process.
        """
        if self.pid is not None:
            os.kill(self.pid, signal.SIGTERM)


class RTSPServer():
    """
    A class for managing an RTSP server process.
    """
    def __init__(self):
        self.name = "mediamtx"
        self.command = [MEDIAMTX_PATH, "rtsp/mediamtx.yml"]
        self.process = Process(self)

    def start(self):
        """
        Start the RTSP server process.
        """
        self.process.start()

    def stop(self):
        """
        Stop the RTSP server process.
        """
        self.process.stop()

    def get_pid(self):
        """
        Get the PID of the RTSP server process.

        Returns:
        - int: The process ID (PID) of the running process.
        """
        if self.process.pid is not None:
            print("PID not found. Have you started the process first?")
            return None

        return self.process.pid


class FFMPEG():
    """
    A class for managing an FFMPEG process.
    """
    def __init__(self):
        self.name = "ffmpeg"
        self.command = [
            self.name, "-re", "-hide_banner",
            "-thread_queue_size", "4096", "-f", "s16le", "-ar", "8000", "-ac", "1", "-i",
            AUDIO_FIFO_PATH,
            "-thread_queue_size", "4096", "-f", "h264", "-i",
            VIDEO_FIFO_PATH,
            "-c:a", "aac", "-b:a", "32000", "-c:v", "libx264", "-preset",
            "ultrafast", "-tune", "zerolatency", "-async", "1",
            "-f", "rtsp", "-rtsp_transport", "tcp", "rtsp://localhost:8554/stream"
        ]
        self.process = Process(self)

    def start(self):
        """
        Start the FFMPEG process.
        """
        self.process.start()

    def stop(self):
        """
        Stop the FFMPEG process.
        """
        self.process.stop()

    def get_pid(self):
        """
        Get the PID of the FFMPEG process.

        Returns:
        - int: The process ID (PID) of the running process.
        """
        if self.process.pid is not None:
            print("PID not found. Have you started the process first?")
            return None

        return self.process.pid
