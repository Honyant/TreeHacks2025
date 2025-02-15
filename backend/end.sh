#!/bin/bash
if [ -f pid.txt ]; then 
    UVICORN_PID=$(cat pid.txt)
    kill $(pgrep -P $UVICORN_PID)
    rm pid.txt src/research.db
    sleep 1
fi