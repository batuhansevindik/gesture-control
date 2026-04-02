#!/bin/bash
echo "$(date) start_cross_lock calisti" >> /home/batuhans/gesture-control/lock_watcher.log
sleep 3
cd /home/batuhans/gesture-control
source /home/batuhans/gesture-control/venv/bin/activate
export LC_ALL=C.UTF-8
export LANG=C.UTF-8
python /home/batuhans/gesture-control/cross_lock.py
