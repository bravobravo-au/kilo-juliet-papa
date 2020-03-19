#!/bin/bash
cd /home/pi/kilo-juliet-papa
source bin/activate
for (( ; ; ))
do
  ./bin/python kilo-juliet-papa.py --config 3607-config.ini
  sleep 10
done
