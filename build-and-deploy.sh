#!/bin/bash
OP=0

docker build . -t spotify-tracking-display:v2

while getopts 'd:' OPTION; do
    case "$OPTION" in
        d) OP=1
    esac
done

docker build . -t spotify-tracking-display:v2

if [ $OP -eq 1 ]
then
    docker compose up -d
else
    docker compose up
fi
