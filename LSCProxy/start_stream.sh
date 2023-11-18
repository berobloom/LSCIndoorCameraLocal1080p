#!/bin/bash

TUTK_BIN="tutk_client"
MEDIAMTX_BIN="mediamtx"
VIDEO_FIFO="video_fifo"
AUDIO_FIFO="audio_fifo"
AV_FIFO="av_fifo"

if [[ ! -n "${CAMERA_UID}" ]] 
then
  echo "UID environment variable not set"
  exit 1
fi

if pgrep "${MEDIAMTX_BIN}" >/dev/null
then
  echo "Mediamtx is already running"
  exit 1
fi

if pgrep "${TUTK_BIN}" >/dev/null
then
  echo "LSC Indoor Camera proxy is already running"
  exit 1
fi

if [[ ! -p "${VIDEO_FIFO}" ]]
then
  mkfifo "${VIDEO_FIFO}"
fi

if [[ ! -p "${AUDIO_FIFO}" ]]
then
  mkfifo "${AUDIO_FIFO}"
fi

if [[ ! -p "${AV_FIFO}" ]]
then
  mkfifo "${AV_FIFO}"
fi

arch=`getconf LONG_BIT`
echo $arch

if [ $arch -eq 32 ];then
  echo install 32 bit lib
  cp -rf ./libs/x86/*.so /usr/lib/
else
  echo install 64bit lib
  cp -rf ./libs/x64/*.so /usr/lib/
fi

./${MEDIAMTX_BIN}&

./${TUTK_BIN} "${CAMERA_UID}"

pkill -9 "${MEDIAMTX}"
pkill -9 "ffmpeg"
