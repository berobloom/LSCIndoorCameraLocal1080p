"""
Constants used in the LSCProxy project.
"""
import pathlib

av_error = {
    "AV_ER_DATA_NOREADY": -20012,
    "AV_ER_LOSED_THIS_FRAME": -20014,
    "AV_ER_SESSION_CLOSE_BY_REMOTE": -20015,
    "AV_ER_REMOTE_TIMEOUT_DISCONNECT": -20016,
}

iotc_error = {
    "IOTC_ER_INVALID_SID": -14
}

settings = {
    "FIFOS_DIR": "fifos",
    "AUDIO_FIFO_PATH": pathlib.Path().absolute() / "fifos/audio_fifo",
    "VIDEO_FIFO_PATH": pathlib.Path().absolute() / "fifos/video_fifo",
    "MEDIAMTX_PATH": pathlib.Path().absolute() / "rtsp/mediamtx",
    "AUDIO_BUF_SIZE": 512,
    "VIDEO_BUF_SIZE": 64000
}

ioctrl = {
    "IOTYPE_USER_IPCAM_SETGRAY_MODE_REQ": 0x5000,
    "IOTYPE_USER_IPCAM_SETSTREAMCTRL_REQ": 0x0320,
    "IOTYPE_USER_IPCAM_START": 0x01FF,
    "IOTYPE_USER_IPCAM_AUDIOSTART": 0x0300
}
