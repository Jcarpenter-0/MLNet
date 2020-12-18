# Mahi Mahi Setup
sudo sysctl -w net.ipv4.ip_forward=1

# cubic test
#sudo sysctl -w net.ipv4.tcp_congestion_control=cubic

iperf3 -s -J --logfile cubic-test.json &

mm-delay 40 iperf3 -c 10.0.0.3 -t 30 -P 1 -C cubic

sudo pkill iperf3

sleep 10

# vegas test
#sudo sysctl -w net.ipv4.tcp_congestion_control=vegas

iperf3 -s -J --logfile vegas-test.json &

mm-delay 40 iperf3 -c 10.0.0.3 -t 30 -P 1 -C vegas

sudo pkill iperf3

#sleep 10

# mixed test
#sudo sysctl -w net.ipv4.tcp_congestion_control=cubic

#iperf3 -s -J --logfile mixed-test.json &

#mm-delay 40 iperf3 -c 10.0.0.3 -t 30 -P 16 &

#sleep 14

#sudo sysctl -w net.ipv4.tcp_congestion_control=vegas

sleep 16

sudo pkill iperf3
