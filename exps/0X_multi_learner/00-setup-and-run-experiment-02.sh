#!/usr/bin/env bash

# Setup Congestion Controls

# Useful links:
# https://securenetweb.wordpress.com/2017/01/24/add-tcp-congestion-control-variant-to-linux-ubuntu-comparing/
# Install example: modprobe -a tcp_westwood
# https://unix.stackexchange.com/questions/278215/add-tcp-congestion-control-variant-to-linux-ubuntu
# https://www.techrepublic.com/article/how-to-enable-tcp-bbr-to-improve-network-speed-on-linux/

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

# Setup MahiMahi Forwarding
sudo sysctl -w net.ipv4.ip_forward=1

# Run Experiment Setup
python3 exp_03_02_environment_differences.py
