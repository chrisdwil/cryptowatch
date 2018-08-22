#!/usr/bin/env bash

while [ 1 -ne 0 ]
do
    python ~/cryptowatch/venv/$1.py > ~/tmp/$1.view_mobile
    clear
    cat ~/tmp/$1.view
    sleep 60
done