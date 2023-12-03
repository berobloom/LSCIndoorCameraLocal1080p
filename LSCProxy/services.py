
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

    def __init__(self, process_object):
        self.process_object = process_object
        self.pid = None


    def start(self):

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

        if self.pid is not None:
            os.kill(self.pid, signal.SIGTERM)


class RTSPServer():

    def __init__(self):
        self.name = "mediamtx"
        self.command = [MEDIAMTX_PATH, "rtsp/mediamtx.yml"]
        self.process = Process(self)


    def start(self):

        self.process.start()


    def stop(self):

        self.process.stop()


class FFMPEG():

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
        self._process.start()


    def stop(self):
        self._process.stop()

    def restart(self):

        print("Restarting ffmpeg...")

        if self._process.pid is not None:
            self.stop()
        new_ffmpeg_thread = threading.Thread(target=self.start)
        new_ffmpeg_thread.daemon = True
        new_ffmpeg_thread.start()

    def enable_flip(self):
        if not self.is_flipped:
            self.command = self._ffmpeg_command_builder("hflip,vflip")
            self.is_flipped = True
            self.restart()

    def disable_flip(self):
        if self.is_flipped:
            self.command = self.command = self._ffmpeg_command_builder()
            self.is_flipped = False
            self.restart()
