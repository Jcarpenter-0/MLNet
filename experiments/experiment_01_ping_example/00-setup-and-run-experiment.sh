#!/usr/bin/env bash

# Setup MahiMahi Forwarding
sudo sysctl -w net.ipv4.ip_forward=1

# Run Experiment Setup
python3 exp-01.py
