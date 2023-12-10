"""
TUTK Framework Wrapper

This module provides a Python wrapper for the TUTK framework,
allowing interaction with an indoor camera.
It defines IOCTRL constants, structures,
and functions required for establishing a connection to the camera,
receiving audio and video streams, and controlling camera settings.

IOCTRL Constants:
    - IOTYPE_USER_IPCAM_SETGRAY_MODE_REQ: Handles nightvision
    - IOTYPE_USER_IPCAM_SETSTREAMCTRL_REQ: Handles quality settings
    - IOTYPE_USER_IPCAM_START: Handles the start of the camera
    - IOTYPE_USER_IPCAM_STOP: Handles the stop of the camera
    - IOTYPE_USER_IPCAM_AUDIOSTART: Handles the start of the audio

IOCTRL Structures:
    - SMsgAVIoctrlSetVideoModeReq: Structure for setting video mode through IOCTRL.
    - SMsgAVIoctrlSetStreamCtrlReq: Structure for setting stream control through IOCTRL.
    - SMsgAVIoctrlAVStream: Structure for AV stream control through IOCTRL.
    - FrameInfoT: Structure for video and audio frame information.

Tutk Class:
    - Defines error_constants, settings, and ioctrl dictionaries.
    - Initializes the TUTK framework and manages IOCTRL commands.
    - Provides functions for disabling/enabling night
      vision, setting video quality, and controlling camera streams.
    - Handles the initiation and cleanup of audio and video streams.
    - Implements functions for IOCTRL commands to control camera settings.
    - Supports initialization, connection, and cleanup of TUTK sessions.

Note:
    - This file uses the ctypes library to interface with the TUTK C library.
    - Error handling is basic and may need to be extended for robustness.

Author:
    Berobloom
"""

# pylint: disable=R0903, R0902, W0201
import ctypes
import os
import sys
import pathlib

# IOCTRL constants
IOTYPE_USER_IPCAM_SETGRAY_MODE_REQ = 0x5000
IOTYPE_USER_IPCAM_SETSTREAMCTRL_REQ = 0x0320
IOTYPE_USER_IPCAM_START = 0x01FF
IOTYPE_USER_IPCAM_STOP = 0x02FF
IOTYPE_USER_IPCAM_AUDIOSTART = 0x0300


# IOCTRL structs
class SMsgAVIoctrlSetVideoModeReq(ctypes.Structure):
    """
    Structure for setting video mode through IOCTRL.
    """
    _fields_ = [("channel", ctypes.c_uint),
                ("mode", ctypes.c_uint)]


class SMsgAVIoctrlSetStreamCtrlReq(ctypes.Structure):
    """
    Structure for setting stream control through IOCTRL.
    """
    _fields_ = [("channel", ctypes.c_uint),
                ("quality", ctypes.c_uint)]


class SMsgAVIoctrlAVStream(ctypes.Structure):
    """
    Structure for AV stream control through IOCTRL.
    """
    _fields_ = [
        ("channel", ctypes.c_uint),
        ("reserved", ctypes.c_ubyte * 4),
    ]


class FrameInfoT(ctypes.Structure):
    """
    Structure for video and audio frame information.
    """
    _fields_ = [
        ("codec_id", ctypes.c_ushort),
        ("flags", ctypes.c_ubyte),
        ("cam_index", ctypes.c_ubyte),
        ("onlineNum", ctypes.c_ubyte),
        ("reserve1", ctypes.c_char * 3),
        ("reserve2", ctypes.c_uint),
        ("timestamp", ctypes.c_uint),
        ("videoWidth", ctypes.c_uint),
        ("videoHeight", ctypes.c_uint),
    ]


class Tutk():
    """
    TUTK Framework Wrapper Class

    This class provides a Python wrapper for the TUTK framework,
    allowing interaction with an indoor camera.
    It defines error_constants, settings,
    and ioctrl dictionaries and implements functions for controlling
    the camera through IOCTRL commands.

    Attributes:
        error_constants (dict): Dictionary of TUTK error constants.
        settings (dict): Dictionary of TUTK settings.
        ioctrl (dict): Dictionary of TUTK IOCTRL commands.

    Methods:
        __init__(self, uid): Initializes the TUTK wrapper with a unique identifier (UID).
        av_client_stop(self): Stops the AV client connection.
        iotc_session_close(self): Closes the IOTC session.
        av_send_ioctrl(self, iotype_command, struct): Sends an IOCTRL command to the AV client.
        ioctrl_disable_nightvision(self): Disables night vision through IOCTRL.
        ioctrl_enable_nightvision(self): Enables night vision through IOCTRL.
        ioctrl_enable_hd_quality(self): Sets video quality to HD through IOCTRL.
        ioctrl_start_camera(self): Starts the camera through IOCTRL.
        ioctrl_stop_camera(self): Stops the camera through IOCTRL.
        ioctrl_start_audio(self): Starts audio streaming through IOCTRL.
        start_ipcam_stream(self): Initiates the camera stream with necessary settings.
        av_initialize(self, max_num_allowed): Initializes the
            AV client with the maximum number of allowed connections.
        iotc_de_initialize(self): De-initializes the TUTK framework.
        clean_audio_buf(self): Cleans the audio buffer.
        clean_video_buf(self): Cleans the video buffer.
        iotc_initialize2(self, num): Initializes the
            IOTC session with the specified number of channels.
        iotc_connect_by_uid_parallel(self): Connects to the camera by UID in parallel mode.
        av_client_start2(self, av_id, av_pass):
            Starts the AV client with the provided AV ID and password.
        create_buf(self, buf_size): Creates a buffer of the specified size.
        av_recv_framedata2(self, buf, buf_size): Receives video frame data into the provided buffer.
        av_recv_audio_data(self, buf, buf_size): Receives audio data into the provided buffer.
        av_check_audio_buf(self): Checks the availability of audio data in the buffer.
    """

    error_constants = {
        "AV_ER_DATA_NOREADY": -20012,
        "AV_ER_LOSED_THIS_FRAME": -20014,
        "AV_ER_SESSION_CLOSE_BY_REMOTE": -20015,
        "AV_ER_REMOTE_TIMEOUT_DISCONNECT": -20016,
        "IOTC_ER_INVALID_SID": -14
    }

    settings = {
        "FIFOS_DIR": "fifos",
        "AUDIO_FIFO_PATH": "fifos/audio_fifo",
        "VIDEO_FIFO_PATH": "fifos/video_fifo",
        "AUDIO_BUF_SIZE": 512,
        "VIDEO_BUF_SIZE": 64000
    }

    ioctrl = {
        "IOTYPE_USER_IPCAM_SETGRAY_MODE_REQ": 0x5000,
        "IOTYPE_USER_IPCAM_SETSTREAMCTRL_REQ": 0x0320,
        "IOTYPE_USER_IPCAM_START": 0x01FF,
        "IOTYPE_USER_IPCAM_AUDIOSTART": 0x0300
    }

    def __init__(self, uid):
        self.graceful_shutdown = False
        self.uid = uid
        self.av_index = None
        self.session_id = None

        lib_iot = pathlib.Path().absolute() / "libs/x64/libIOTCAPIs_ALL.so"

        self._iot = ctypes.CDLL(lib_iot, mode=os.RTLD_LAZY)

        self._iot.avInitialize.argtypes = [ctypes.c_int]

        self._iot.avDeInitialize.argtypes = []
        self._iot.IOTC_DeInitialize.argtypes = []

        self._iot.IOTC_Initialize2.argtypes = [ctypes.c_int]
        self._iot.IOTC_Initialize2.restype = ctypes.c_int

        self._iot.IOTC_Get_SessionID.argtypes = []
        self._iot.IOTC_Get_SessionID.restype = ctypes.c_int

        self._iot.IOTC_Connect_ByUID_Parallel.argtypes = [ctypes.c_char_p, ctypes.c_int]
        self._iot.IOTC_Connect_ByUID_Parallel.restype = ctypes.c_int

        self._iot.avSendIOCtrl.argtypes = [ctypes.c_int, ctypes.c_int,
                                           ctypes.c_char_p, ctypes.c_size_t]

        self._iot.avClientStart2.argtypes = [ctypes.c_int, ctypes.c_char_p, ctypes.c_char_p,
                                             ctypes.c_int, ctypes.POINTER(ctypes.c_uint), ctypes.c_int,
                                             ctypes.POINTER(ctypes.c_int)]
        self._iot.avClientStart2.restype = ctypes.c_int

        self._iot.avClientStop.argtypes = [ctypes.c_int]
        self._iot.IOTC_Session_Close.argtypes = [ctypes.c_int]

        self._iot.avRecvFrameData2.argtypes = [ctypes.c_int, ctypes.c_void_p,
                                               ctypes.c_int,
                                               ctypes.POINTER(ctypes.c_int),
                                               ctypes.POINTER(ctypes.c_int),
                                               ctypes.c_char_p, ctypes.c_size_t,
                                               ctypes.POINTER(ctypes.c_int),
                                               ctypes.POINTER(ctypes.c_uint)]
        self._iot.avRecvFrameData2.restype = ctypes.c_int

        self._iot.avRecvAudioData.argtypes = (ctypes.c_int,
                                              ctypes.c_char_p, ctypes.c_int,
                                              ctypes.POINTER(FrameInfoT),
                                              ctypes.c_int,
                                              ctypes.POINTER(ctypes.c_uint))
        self._iot.avRecvAudioData.restype = ctypes.c_int

        self._iot.avCheckAudioBuf.argtypes = [ctypes.c_int]
        self._iot.avCheckAudioBuf.restype = ctypes.c_int

        self._iot.avClientCleanVideoBuf.argtypes = [ctypes.c_int]
        self._iot.avClientCleanAudioBuf.argtypes = [ctypes.c_int]

        self._video_frame_info = FrameInfoT()
        self._video_frm_no = ctypes.c_uint(0)
        self._video_out_buf_size = ctypes.c_int(0)
        self._video_out_frm_size = ctypes.c_int(0)
        self._video_out_frm_info_size = ctypes.c_int(0)

        self._audio_out_frm_info_size = ctypes.c_int(16)
        self._audio_frame_info = FrameInfoT()
        self._audio_frm_no = ctypes.c_uint()

        self._srv_type = ctypes.c_uint()
        self._resend = ctypes.c_int(-1)

    def av_client_stop(self):
        """
        Stops the AV client connection.

        Returns:
            None
        """

        self._iot.avClientStop(self.av_index)

    def iotc_session_close(self):
        """
        Closes the IOTC session.

        Returns:
            None
        """

        self._iot.IOTC_Session_Close(self.session_id)

    def av_send_ioctrl(self, iotype_command, struct):
        """
        Sends an IOCTRL command to the AV client.

        Args:
            iotype_command (int): IOCTRL command type.
            struct: IOCTRL command structure.

        Returns:
            bool: True if the command was sent successfully, False otherwise.
        """

        struct_bytes = bytes(struct)
        status = self._iot.avSendIOCtrl(self.av_index, iotype_command,
                                        struct_bytes, len(struct_bytes))

        if status < 0:
            print(f"Error status: {status}")
            return False

        return True

    def ioctrl_disable_nightvision(self):
        """
        Disables night vision through IOCTRL.

        Returns:
            int: Status code of the IOCTRL command.
        """

        io_nightvision = SMsgAVIoctrlSetVideoModeReq()
        io_nightvision.channel = 1
        io_nightvision.mode = 1

        status = self.av_send_ioctrl(IOTYPE_USER_IPCAM_SETGRAY_MODE_REQ, io_nightvision)

        return status

    def ioctrl_enable_nightvision(self):
        """
        Enables night vision through IOCTRL.

        Returns:
            int: Status code of the IOCTRL command.
        """

        io_nightvision = SMsgAVIoctrlSetVideoModeReq()
        io_nightvision.channel = 0
        io_nightvision.mode = 0

        status = self.av_send_ioctrl(IOTYPE_USER_IPCAM_SETGRAY_MODE_REQ, io_nightvision)

        return status

    def ioctrl_enable_hd_quality(self):
        """
        Sets video quality to HD through IOCTRL.

        Returns:
            int: Status code of the IOCTRL command.
        """

        io_quality = SMsgAVIoctrlSetStreamCtrlReq()
        io_quality.channel = 0
        io_quality.quality = 2

        status = self.av_send_ioctrl(IOTYPE_USER_IPCAM_SETSTREAMCTRL_REQ, io_quality)

        return status

    def ioctrl_start_camera(self):
        """
        Starts the camera through IOCTRL.

        Returns:
            int: Status code of the IOCTRL command.
        """

        self.clean_audio_buf()
        self.clean_video_buf()
        io_camera = SMsgAVIoctrlAVStream()
        io_camera.channel = 1

        status = self.av_send_ioctrl(IOTYPE_USER_IPCAM_START, io_camera)

        return status

    def ioctrl_stop_camera(self):
        """
        Stops the camera through IOCTRL.

        Returns:
            int: Status code of the IOCTRL command.
        """

        io_camera = SMsgAVIoctrlAVStream()
        io_camera.channel = 1

        status = self.av_send_ioctrl(IOTYPE_USER_IPCAM_STOP, io_camera)

        return status

    def ioctrl_start_audio(self):
        """
        Starts audio streaming through IOCTRL.

        Returns:
            int: Status code of the IOCTRL command.
        """

        io_audio = SMsgAVIoctrlAVStream()
        io_audio.channel = 1

        status = self.av_send_ioctrl(IOTYPE_USER_IPCAM_AUDIOSTART, io_audio)

        return status

    def start_ipcam_stream(self):
        """
        Initiates the camera stream with necessary settings.

        Returns:
            bool: True if the camera stream was initiated successfully, False otherwise.
        """

        if not self.ioctrl_disable_nightvision():
            print("Cannot start camera. Error while disabling nightvision")
            return False

        if not self.ioctrl_enable_hd_quality():
            print("Cannot start camera. Error while setting quality to HD")
            return False

        if not self.ioctrl_start_camera():
            print("Cannot start camera. Camera error")
            return False

        if not self.ioctrl_start_audio():
            print("Cannot start camera. Error while starting audio")
            return False

        return True

    def av_initialize(self, max_num_allowed):
        """
        Initializes the AV client with the maximum number of allowed connections.

        Args:
            max_num_allowed (int): Maximum number of allowed connections.

        Returns:
            None
        """

        self._iot.avInitialize(max_num_allowed)

    def iotc_de_initialize(self):
        """
        De-initializes the TUTK framework.

        Returns:
            None
        """

        self._iot.avDeInitialize()
        self._iot.IOTC_DeInitialize()

    def clean_audio_buf(self):
        """
        Cleans the audio buffer.

        Returns:
            None
        """

        self._iot.avClientCleanAudioBuf(self.av_index)

    def clean_video_buf(self):
        """
        Cleans the video buffer.

        Returns:
            None
        """

        self._iot.avClientCleanVideoBuf(self.av_index)

    def iotc_initialize2(self, num):
        """
        Initializes the IOTC session with the specified number of channels.

        Args:
            num (int): Number of channels.

        Returns:
            None
        """

        status = self._iot.IOTC_Initialize2(num)
        if status != 0:
            print("IOTCAPIs_Device exit...!!")
            sys.exit(1)

    def iotc_connect_by_uid_parallel(self):
        """
        Connects to the camera by UID in parallel mode.

        Returns:
            None
        """

        tmp_session_id = self._iot.IOTC_Get_SessionID()
        if tmp_session_id < 0:
            print("Get session ID failed")
            sys.exit(1)
        new_session_id = self._iot.IOTC_Connect_ByUID_Parallel(self.uid.encode('utf-8'),
                                                               tmp_session_id)
        if new_session_id < 0:
            print(f"Connect by UID failed. Error code: {new_session_id}")
            sys.exit(1)
        else:
            self.session_id = new_session_id

    def av_client_start2(self, av_id, av_pass):
        """
        Starts the AV client with the provided AV ID and password.

        Args:
            av_id (str): AV ID.
            av_pass (str): AV password.

        Returns:
            None
        """

        timeout = 20
        service_type = 0
        self.av_index = self._iot.avClientStart2(self.session_id, av_id.encode('utf-8'),
                                                 av_pass.encode('utf-8'), timeout, ctypes.byref(self._srv_type),
                                                 service_type, ctypes.byref(self._resend))
        if self.av_index < 0:
            print(f"avClientStart2 failed[{self.av_index}]")
            sys.exit(1)

    def create_buf(self, buf_size):
        """
        Creates a buffer of the specified size.

        Args:
            buf_size (int): Size of the buffer.

        Returns:
            ctypes.Array: Created buffer.
        """

        buf = ctypes.create_string_buffer(buf_size)
        return buf

    def av_recv_framedata2(self, buf, buf_size):
        """
        Receives video frame data into the provided buffer.

        Args:
            buf: Buffer for receiving data.
            buf_size (int): Size of the buffer.

        Returns:
            int: Status code of the AV reception.
        """

        status = self._iot.avRecvFrameData2(self.av_index, buf, buf_size,
                                            ctypes.byref(self._video_out_buf_size),
                                            ctypes.byref(self._video_out_frm_size),
                                            ctypes.cast(ctypes.byref(self._video_frame_info),
                                                        ctypes.c_char_p), ctypes.sizeof(FrameInfoT),
                                            ctypes.byref(self._video_out_frm_info_size),
                                            ctypes.byref(self._video_frm_no))
        return status

    def av_recv_audio_data(self, buf, buf_size):
        """
        Receives audio data into the provided buffer.

        Args:
            buf: Buffer for receiving data.
            buf_size (int): Size of the buffer.

        Returns:
            int: Status code of the AV reception.
        """

        status = self._iot.avRecvAudioData(self.av_index, ctypes.cast(buf, ctypes.c_char_p),
                                           buf_size,
                                           self._audio_frame_info,
                                           self._audio_out_frm_info_size,
                                           self._audio_frm_no)
        return status

    def av_check_audio_buf(self):
        """
        Checks the availability of audio data in the buffer.

        Returns:
            int: Status code of the audio buffer check.
        """

        status = self._iot.avCheckAudioBuf(self.av_index)
        return status
