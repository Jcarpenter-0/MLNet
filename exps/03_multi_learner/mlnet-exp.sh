#!/usr/bin/env bash

echo "Current CC's Configured on Host"
sysctl net.ipv4.tcp_available_congestion_control

echo "Current Congestion Control"
sysctl net.ipv4.tcp_congestion_control

echo "setup each, assign then revert"
sudo sysctl -w net.ipv4.tcp_congestion_control=bbr
sudo sysctl -w net.ipv4.tcp_congestion_control=vegas
sudo sysctl -w net.ipv4.tcp_congestion_control=westwood
sudo sysctl -w net.ipv4.tcp_congestion_control=lp
sudo sysctl -w net.ipv4.tcp_congestion_control=bic
sudo sysctl -w net.ipv4.tcp_congestion_control=htcp
sudo sysctl -w net.ipv4.tcp_congestion_control=veno
sudo sysctl -w net.ipv4.tcp_congestion_control=illinois

# Revert to default
sudo sysctl -w net.ipv4.tcp_congestion_control=cubic

echo "Now available CC's"
sysctl net.ipv4.tcp_available_congestion_control
echo "Current Congestion Control"
sysctl net.ipv4.tcp_congestion_control

sudo sysctl -w net.ipv4.ip_forward=1

sudo rm -r ./tmp/*

mkdir -m 777 ./tmp/

# Eval
python3 one-cc-benchmark-exp.py

python3 one-learner-exp.py

# copy off one of the solos
cp -R ./tmp/one-learner/ ./tmp/one-learner-2/

python3 two-cc-benchmark-exp.py

python3 two-learner-exp.py

python3 two-solo-learners-exp.py

python3 analyze.py
