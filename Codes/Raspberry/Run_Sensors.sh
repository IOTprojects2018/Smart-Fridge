#!/bin/bash
python3 ImageClient.py & 
python RaspberryPublisher.py &
wait
