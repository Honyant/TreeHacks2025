#!/bin/bash
# Start script for the application

if [ -f pid.txt ]; then 
    UVICORN_PID=$(cat pid.txt)
    kill $(pgrep -P $UVICORN_PID)
    rm pid.txt
    sleep 1
fi
nohup bash -c "source .venv/bin/activate && cd src && uvicorn main:app --reload" > output.log 2>&1 &
echo $! > pid.txt