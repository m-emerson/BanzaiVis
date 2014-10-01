#!/bin/bash

NAME="BanzaiVis"
FLASKDIR=../banzaivis/
SOCKFILE=../banzaivis/sock
VENVDIR=~/.Virtualenvs/BanzaiVis/
USER=mscook
GROUP=staff
NUM_WORKERS=3

echo "Starting $NAME"

# activate the virtualenv
cd $VENVDIR
source bin/activate

export PYTHONPATH=$FLASKDIR:$PYTHONPATH

# Create the run directory if it doesn't exist
RUNDIR=$(dirname $SOCKFILE)
test -d $RUNDIR || mkdir -p $RUNDIR

# Start your unicorn
exec gunicorn application:app -b 127.0.0.1:8888 \
        --name $NAME \
        --workers $NUM_WORKERS \
        --user=$USER --group=$GROUP \
        --log-level=debug \
        --bind=unix:$SOCKFILE
