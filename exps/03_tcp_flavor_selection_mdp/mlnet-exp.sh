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
python3 eval-exp.py

# First Test
python3 naive-exp.py

python3 constrained-exp.py

# Second Test
python3 mdp-exp.py

# Do the data processing
python3 analyze.py ./tmp/mm-iperf-benchmark/learner/Traces/ ./tmp/mm-iperf-naive/learner/Traces/ ./tmp/mm-iperf-constrained/learner/Traces/ ./tmp/mm-iperf-mdp/learner/Traces/

#python3 ../00_cc_benchmark/01-aggregate-mahimahi-traces.py ./tmp/mdp-up-log ./tmp/

#python3 ../00_cc_benchmark/01-aggregate-mahimahi-traces.py ./tmp/naive-up-log ./tmp/

# trunc files
#python3 ./01a-trunc-group.py ./tmp/mdp-up-log.csv ./tmp/mdp-up-log-trunc.csv

#python3 ./01a-trunc-group.py ./tmp/naive-up-log.csv ./tmp/naive-up-log-trunc.csv

#python3 ../00_cc_benchmark/02-calculate-reward-from-mahimahi-trace.py ./tmp/mdp-up-log-agg.csv ./tmp/

#python3 ../00_cc_benchmark/02-calculate-reward-from-mahimahi-trace.py ./tmp/naive-up-log-agg.csv ./tmp/

#python3 ../00_cc_benchmark/02-calculate-reward-from-mahimahi-trace.py ./tmp/mdp-up-log-trunc-agg.csv ./tmp/

#python3 ../00_cc_benchmark/02-calculate-reward-from-mahimahi-trace.py ./tmp/mdp-up-log-trunc-agg.csv ./tmp/
