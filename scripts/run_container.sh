#!/bin/bash

# on host system run `xhost +` to grant permission to connect to X

docker run -v /tmp/.X11-unix:/tmp/.X11-unix -e DISPLAY=$DISPLAY -it virgesmith/neworder

