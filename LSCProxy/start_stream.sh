#!/bin/bash

TUTK_BIN="tutk_client"
MEDIAMTX_BIN="mediamtx"

if [[ ! -n "${CAMERA_UID}" ]] 
then
  echo "UID environment variable not set"
fi

if pgrep "${MEDIAMTX_BIN}" >/dev/null
then
  echo "Go2RTC is already running"
  exit 1
fi

if pgrep "${TUTK_BIN}" >/dev/null
then
  echo "LSC Indoor Camera proxy is already running"
  exit 1
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
