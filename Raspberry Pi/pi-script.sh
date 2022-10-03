#!/bin/bash

sudo crontab -e

@reboot /home/pi/Desktop/rtsp-simple-server  /home/pi/Desktop/rtsp-simple-server.yml                                                                                                                                                                                     
@reboot libcamera-vid --width=1024 --height=768  --timeout 0 --vflip=1 --inline --framerate=10 -o - | ffmpeg -i /dev/stdin -preset ultrafast -c copy -f rtsp rtsp://127.0.0.1:8554/cam

sudo chmod a+x FILENAME
