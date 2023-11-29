"""
Tutk Module

This module provides a Tutk class for managing TUTK IoT connections.
It includes IOCTRL structs and methods
for initializing, connecting, and interacting with TUTK devices.

IOCTRL Structs:
- SMsgAVIoctrlSetVideoModeReq: Struct for setting video mode.
- SMsgAVIoctrlSetStreamCtrlReq: Struct for setting stream control.
- SMsgAVIoctrlAVStream: Struct for AV stream control.
- FRAMEINFO_t: Struct for video and audio frame information.

Tutk Class:
- Tutk: Class for managing TUTK IoT connections.

Attributes:
- graceful_shutdown (bool): Flag to indicate if a graceful shutdown is requested.
- uid (str): The unique identifier for the device.
- av_index (int): The AV index for the TUTK connection.
- session_id (int): The session ID for the TUTK connection.
- srv_type (ctypes.c_uint): Service type for the TUTK connection.
- resend (ctypes.c_int): Resend parameter for the TUTK connection.
- iot (ctypes.CDLL): TUTK IoT library.

Methods:
- av_client_exit(): Exit the TUTK AV client.
- av_client_stop(): Stop the TUTK AV client.
- iotc_session_close(): Close the TUTK IoT session.
- av_send_ioctrl(iotype_command, struct): Send IOCTRL command to the TUTK device.
- av_initialize(max_num_allowed): Initialize the TUTK AV library.
- iotc_de_initialize(): Deinitialize the TUTK IoT and AV libraries.
- clean_audio_buf(): Clean the TUTK audio buffer.
- clean_video_buf(): Clean the TUTK video buffer.
- iotc_initialize2(num): Initialize the TUTK IoT library.
- iotc_connect_by_uid_parallel(): Connect to the TUTK device using UID in parallel mode.
- av_client_start2(av_id, av_pass): Start the TUTK AV client.
- create_buf(buf_size): Create a buffer of a specified size.
- av_recv_framedata2(buf, buf_size): Receive video frame data from the TUTK device.
- av_recv_audio_data(buf, buf_size): Receive audio data from the TUTK device.
- av_check_audio_buf(): Check the TUTK audio buffer.
"""
# pylint: disable=R0903, R0902
import ctypes
import os
import sys
import pathlib


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
    Tutk class for managing TUTK IoT connections.

    Args:
    - uid (str): The unique identifier for the device.

    Attributes:
    - graceful_shutdown (bool): Flag to indicate if a graceful shutdown is requested.
    - uid (str): The unique identifier for the device.
    - av_index (int): The AV index for the TUTK connection.
    - session_id (int): The session ID for the TUTK connection.
    - srv_type (ctypes.c_uint): Service type for the TUTK connection.
    - resend (ctypes.c_int): Resend parameter for the TUTK connection.
    - iot (ctypes.CDLL): TUTK IoT library.

    Methods:
    - av_client_exit(): Exit the TUTK AV client.
    - av_client_stop(): Stop the TUTK AV client.
    - iotc_session_close(): Close the TUTK IoT session.
    - av_send_ioctrl(iotype_command, struct): Send IOCTRL command to the TUTK device.
    - av_initialize(max_num_allowed): Initialize the TUTK AV library.
    - iotc_de_initialize(): Deinitialize the TUTK IoT and AV libraries.
    - clean_audio_buf(): Clean the TUTK audio buffer.
    - clean_video_buf(): Clean the TUTK video buffer.
    - iotc_initialize2(num): Initialize the TUTK IoT library.
    - iotc_connect_by_uid_parallel(): Connect to the TUTK device using UID in parallel mode.
    - av_client_start2(av_id, av_pass): Start the TUTK AV client.
    - create_buf(buf_size): Create a buffer of a specified size.
    - av_recv_framedata2(buf, buf_size): Receive video frame data from the TUTK device.
    - av_recv_audio_data(buf, buf_size): Receive audio data from the TUTK device.
    - av_check_audio_buf(): Check the TUTK audio buffer.
    """
    def __init__(self, uid):
        self.graceful_shutdown = False

        self.uid = uid
        self.av_index = None
        self.session_id = None

        lib_iot = pathlib.Path().absolute() / "libs/x64/libIOTCAPIs_ALL.so"
        self.iot = ctypes.CDLL(lib_iot, mode=os.RTLD_LAZY)

        self.iot.avInitialize.argtypes = [ctypes.c_int]

        self.iot.avDeInitialize.argtypes = []
        self.iot.IOTC_DeInitialize.argtypes = []

        self.iot.IOTC_Initialize2.argtypes = [ctypes.c_int]
        self.iot.IOTC_Initialize2.restype = ctypes.c_int

        self.iot.IOTC_Get_SessionID.argtypes = []
        self.iot.IOTC_Get_SessionID.restype = ctypes.c_int

        self.iot.IOTC_Connect_ByUID_Parallel.argtypes = [ctypes.c_char_p, ctypes.c_int]
        self.iot.IOTC_Connect_ByUID_Parallel.restype = ctypes.c_int

        self.iot.avSendIOCtrl.argtypes = [ctypes.c_int, ctypes.c_int,
        ctypes.c_char_p, ctypes.c_size_t]

        self.iot.avClientStart2.argtypes = [ctypes.c_int, ctypes.c_char_p, ctypes.c_char_p,
                                        ctypes.c_int, ctypes.POINTER(ctypes.c_uint), ctypes.c_int,
                                        ctypes.POINTER(ctypes.c_int)]
        self.iot.avClientStart2.restype = ctypes.c_int

        self.iot.avClientExit.argtypes = [ctypes.c_int, ctypes.c_int]
        self.iot.avClientStop.argtypes = [ctypes.c_int]
        self.iot.IOTC_Session_Close.argtypes = [ctypes.c_int]

        self.iot.avRecvFrameData2.argtypes = [ctypes.c_int, ctypes.c_void_p,
                                            ctypes.c_int,
                                            ctypes.POINTER(ctypes.c_int),
                                            ctypes.POINTER(ctypes.c_int),
                                            ctypes.c_char_p, ctypes.c_size_t,
                                            ctypes.POINTER(ctypes.c_int),
                                            ctypes.POINTER(ctypes.c_uint)]
        self.iot.avRecvFrameData2.restype = ctypes.c_int

        self.iot.avRecvAudioData.argtypes = (ctypes.c_int,
                                            ctypes.c_char_p, ctypes.c_int,
                                            ctypes.POINTER(FrameInfoT),
                                            ctypes.c_int,
                                            ctypes.POINTER(ctypes.c_uint))
        self.iot.avRecvAudioData.restype = ctypes.c_int

        self.iot.avCheckAudioBuf.argtypes = [ctypes.c_int]
        self.iot.avCheckAudioBuf.restype = ctypes.c_int

        self.iot.avClientCleanVideoBuf.argtypes = [ctypes.c_int]
        self.iot.avClientCleanAudioBuf.argtypes = [ctypes.c_int]

        self.video_frame_info = FrameInfoT()
        self.video_frm_no = ctypes.c_uint(0)
        self.video_out_buf_size = ctypes.c_int(0)
        self.video_out_frm_size = ctypes.c_int(0)
        self.video_out_frm_info_size = ctypes.c_int(0)

        self.audio_out_frm_info_size = ctypes.c_int(16)
        self.audio_frame_info = FrameInfoT()
        self.audio_frm_no = ctypes.c_uint()

        self.srv_type = ctypes.c_uint()
        self.resend = ctypes.c_int(-1)


    def av_client_exit(self):
        """
        Exit the TUTK AV client.
        """
        self.iot.avClientExit(self.session_id, self.av_index)


    def av_client_stop(self):
        """
        Stop the TUTK AV client.
        """
        self.iot.avClientStop(self.av_index)


    def iotc_session_close(self):
        """
        Close the TUTK IoT session.
        """
        self.iot.IOTC_Session_Close(self.session_id)


    def av_send_ioctrl(self, iotype_command, struct):
        """
        Send IOCTRL command to the TUTK device.

        Args:
        - iotype_command (int): IOCTRL command type.
        - struct (ctypes.Structure): IOCTRL command structure.

        Returns:
        - bool: True if successful, False otherwise.
        """
        struct_bytes = bytes(struct)
        status = self.iot.avSendIOCtrl(self.av_index, iotype_command,
                                    struct_bytes, len(struct_bytes))

        if status < 0:
            print(f"Error status: {status}")
            return False

        return True


    def av_initialize(self, max_num_allowed):
        """
        Initialize the TUTK AV library.

        Args:
        - max_num_allowed (int): Maximum number of allowed connections.
        """
        self.iot.avInitialize(max_num_allowed)


    def iotc_de_initialize(self):
        """
        Deinitialize the TUTK IoT and AV libraries.
        """
        self.iot.avDeInitialize()
        self.iot.IOTC_DeInitialize()


    def clean_audio_buf(self):
        """
        Clean the TUTK audio buffer.
        """
        self.iot.avClientCleanAudioBuf(self.av_index)


    def clean_video_buf(self):
        """
        Clean the TUTK video buffer.
        """
        self.iot.avClientCleanVideoBuf(self.av_index)


    def iotc_initialize2(self, num):
        """
        Initialize the TUTK IoT library.

        Args:
        - num (int): Initialization parameter.
        """
        status = self.iot.IOTC_Initialize2(num)
        if status != 0:
            print("IOTCAPIs_Device exit...!!")
            sys.exit(1)


    def iotc_connect_by_uid_parallel(self):
        """
        Connect to the TUTK device using UID in parallel mode.
        """
        tmp_session_id = self.iot.IOTC_Get_SessionID()
        if tmp_session_id < 0:
            print("Get session ID failed")
            sys.exit(1)
        new_session_id = self.iot.IOTC_Connect_ByUID_Parallel(self.uid.encode('utf-8'),
                            tmp_session_id)
        if new_session_id < 0:
            print(f"Connect by UID failed. Error code: {new_session_id}")
            sys.exit(1)
        else:
            self.session_id = new_session_id


    def av_client_start2(self, av_id, av_pass):
        """
        Start the TUTK AV client.

        Args:
        - av_id (str): AV ID.
        - av_pass (str): AV password.
        """
        timeout = 20
        service_type = 0
        self.av_index = self.iot.avClientStart2(self.session_id, av_id.encode('utf-8'),
                            av_pass.encode('utf-8'), timeout, ctypes.byref(self.srv_type),
                            service_type, ctypes.byref(self.resend))
        if self.av_index < 0:
            print(f"avClientStart2 failed[{self.av_index}]")
            sys.exit(1)


    def create_buf(self, buf_size):
        """
        Create a buffer of a specified size.

        Args:
        - buf_size (int): Size of the buffer.

        Returns:
        - ctypes.create_string_buffer: The created buffer.
        """
        buf = ctypes.create_string_buffer(buf_size)
        return buf


    def av_recv_framedata2(self, buf, buf_size):
        """
        Receive video frame data from the TUTK device.

        Args:
        - buf (ctypes.create_string_buffer): Buffer to store the frame data.
        - buf_size (int): Size of the buffer.

        Returns:
        - int: Status of the operation.
        """
        status = self.iot.avRecvFrameData2(self.av_index, buf, buf_size,
                                    ctypes.byref(self.video_out_buf_size),
                                    ctypes.byref(self.video_out_frm_size),
                                    ctypes.cast(ctypes.byref(self.video_frame_info),
                                    ctypes.c_char_p), ctypes.sizeof(FrameInfoT),
                                    ctypes.byref(self.video_out_frm_info_size),
                                    ctypes.byref(self.video_frm_no))
        return status


    def av_recv_audio_data(self, buf, buf_size):
        """
        Receive audio data from the TUTK device.

        Args:
        - buf (ctypes.create_string_buffer): Buffer to store the audio data.
        - buf_size (int): Size of the buffer.

        Returns:
        - int: Status of the operation.
        """
        status = self.iot.avRecvAudioData(self.av_index, ctypes.cast(buf, ctypes.c_char_p),
                                            buf_size,
                                            self.audio_frame_info,
                                            self.audio_out_frm_info_size,
                                            self.audio_frm_no)
        return status


    def av_check_audio_buf(self):
        """
        Check the TUTK audio buffer.

        Returns:
        - int: Status of the operation.
        """
        status = self.iot.avCheckAudioBuf(self.av_index)
        return status
