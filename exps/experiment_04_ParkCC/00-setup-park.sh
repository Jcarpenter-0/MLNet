 mm-delay 25 mm-link ./const48.mahi ./const48.mahi --uplink-queue=droptail --uplink-queue-args="packets=2000" --downlink-queue=droptail --downlink-queue-args="packets=2000"

 python3 ../../apps/Iperf3.py -c 192.168.1.249 100000 http://192.168.1.249:8080