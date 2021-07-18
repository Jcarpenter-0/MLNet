#!/usr/bin/env bash

sudo sysctl -w net.ipv4.ip_forward=1

sudo rm -r ./tmp/*

mkdir -m 777 ./tmp/

python3 benchmark-exp.py

python3 analyze.py