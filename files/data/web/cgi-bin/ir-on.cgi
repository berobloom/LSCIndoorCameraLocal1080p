#!/bin/sh

# Set the Content-type header
echo "Content-type: text/html"
echo

echo 1 > /sys/class/gpio/GPIO19/value
echo 1 > /sys/class/gpio/GPIO3/value
echo 0 > /sys/class/gpio/GPIO20/value
sleep 1
echo 0 > /sys/class/gpio/GPIO19/value
echo 0 > /sys/class/gpio/GPIO20/value