#!/bin/bash

# Kill any previous ffmpeg or libcamera-vid streams 
pkill -f "libcamera-vid"
pkill -f "ffmpeg"

# Pause to ensure processes are killed
sleep 1

# Run streaming command
libcamera-vid -t 0 \
--width 1280 --height 720 --framerate 30 \
--codec yuv420 --inline -o - \
| ffmpeg -f rawvideo -pix_fmt yuv420p -s 1280x720 -i - \
-c:v libx264 -preset veryfast -tune zerolatency -b:v 2500k \
-f flv rtmp://54.253.200.89/hls/test