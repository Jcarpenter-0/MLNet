#!/usr/bin/env bash

# Setup Congestion Controls

# Useful links:
# https://securenetweb.wordpress.com/2017/01/24/add-tcp-congestion-control-variant-to-linux-ubuntu-comparing/
# Install example: modprobe -a tcp_westwood
# https://unix.stackexchange.com/questions/278215/add-tcp-congestion-control-variant-to-linux-ubuntu
# https://www.techrepublic.com/article/how-to-enable-tcp-bbr-to-improve-network-speed-on-linux/

#CURDIR=$PWD
#cd ../../
#sh ./01-setup-python-project-dir.sh
#cd $CURDIR

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

python3 mlnet-exp.py

# Post test data processing

python3 ../00_cc_benchmark/01-aggregate-mahimahi-traces.py ./tmp/mm-vegas-iperf3-up-log ./tmp/
python3 ../00_cc_benchmark/01-aggregate-mahimahi-traces.py ./tmp/mm-vegas-iperf-up-log ./tmp/

python3 ../00_cc_benchmark/02-calculate-reward-from-mahimahi-trace.py ./tmp/mm-vegas-iperf3-up-log.csv ./tmp/
python3 ../00_cc_benchmark/02-calculate-reward-from-mahimahi-trace.py ./tmp/mm-vegas-iperf-up-log.csv ./tmp/

# create trunc files
python3 ./01a-trunc-group.py ./tmp/mm-vegas-iperf3-up-log.csv ./tmp/mm-vegas-iperf3-up-log-trunc.csv
python3 ./01a-trunc-group.py ./tmp/mm-vegas-iperf-up-log.csv ./tmp/mm-vegas-iperf-up-log-trunc.csv

# Get rewards for trunc files
python3 ../00_cc_benchmark/02-calculate-reward-from-mahimahi-trace.py ./tmp/mm-vegas-iperf3-up-log-trunc.csv ./tmp/
python3 ../00_cc_benchmark/02-calculate-reward-from-mahimahi-trace.py ./tmp/mm-vegas-iperf-up-log-trunc.csv ./tmp/

# create merge file
python3 ./01b-merge-files.py ./tmp/mm-vegas-iperfs-reward-trunc.csv ./tmp/mm-vegas-iperf-up-log-trunc-reward-only-group-10.csv ./tmp/mm-vegas-iperf3-up-log-trunc-reward-only-group-10.csv
python3 ./01c-merge-files-tput.py ./tmp/mm-vegas-iperfs-tput-trunc.csv ./tmp/mm-vegas-iperf-up-log-trunc.csv ./tmp/mm-vegas-iperf3-up-log-trunc.csv
