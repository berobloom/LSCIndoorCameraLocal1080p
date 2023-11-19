#!/bin/bash

arch=`getconf LONG_BIT`

if [ $arch -eq 32 ];then
  echo install 32 bit lib
  cp -rf ../libs/x86/*.so /usr/lib/
else
  echo install 64bit lib
  cp -rf ../libs/x64/*.so /usr/lib/
fi
