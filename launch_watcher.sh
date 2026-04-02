#!/bin/bash
LOGFILE="/home/batuhans/gesture-control/lock_watcher.log"

echo "$(date) launch_watcher calisti" >> "$LOGFILE"
sleep 12

pkill -f "/home/batuhans/gesture-control/lock_watcher.sh"

nohup /bin/bash /home/batuhans/gesture-control/lock_watcher.sh >> "$LOGFILE" 2>&1 &
echo "$(date) lock_watcher nohup ile baslatildi" >> "$LOGFILE"
