#!/bin/bash
sleep 8

LOGFILE="/home/batuhans/gesture-control/lock_watcher.log"
START_SCRIPT="/home/batuhans/gesture-control/start_cross_lock.sh"
USERNAME="batuhans"

get_session_id() {
    loginctl list-sessions --no-legend | awk -v user="$USERNAME" '$3 == user {print $1; exit}'
}

is_locked() {
    SESSION_ID="$(get_session_id)"
    if [ -z "$SESSION_ID" ]; then
        echo "unknown"
        return
    fi

    loginctl show-session "$SESSION_ID" -p LockedHint --value 2>/dev/null
}

is_cross_running() {
    pgrep -f "/home/batuhans/gesture-control/cross_lock.py" > /dev/null
}

start_cross_lock() {
    if ! is_cross_running; then
        echo "$(date) START cross_lock" >> "$LOGFILE"
        nohup "$START_SCRIPT" >> "$LOGFILE" 2>&1 &
    else
        echo "$(date) cross_lock zaten calisiyor" >> "$LOGFILE"
    fi
}

stop_cross_lock() {
    if is_cross_running; then
        echo "$(date) STOP cross_lock" >> "$LOGFILE"
        pkill -f "/home/batuhans/gesture-control/cross_lock.py"
    fi
}

echo "$(date) lock_watcher basladi" >> "$LOGFILE"

while true; do
    LOCK_STATE="$(is_locked)"

    if [ "$LOCK_STATE" = "yes" ]; then
        stop_cross_lock
    elif [ "$LOCK_STATE" = "no" ]; then
        start_cross_lock
    else
        echo "$(date) session bulunamadi" >> "$LOGFILE"
    fi

    sleep 2
done
