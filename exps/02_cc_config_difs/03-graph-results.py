import matplotlib.pyplot as plt
import json
import numpy as np
import pandas as pd

plt.style.use('seaborn-whitegrid')

# Graph the Reward vs Actions for mm and Iperfs
df2 = pd.read_csv('./tmp/mm-vegas-iperfs-reward-trunc.csv')

# Iperf3, Iperf2
colors = ['red', 'green']

ax = df2.plot(style=['--','--'], color=colors, title='Network Congestion Control - Application Difference')
ax.set_ylabel('Reward')
ax.set_xlabel('Number of Actions (10ms)')

plt.yticks(np.arange(6, 18, step=2))
plt.xticks(np.arange(0.0, 130, step=10))
plt.savefig('./tmp/benchmark-reward-between-application-configs-mm-iperfs.png')
plt.close()

# Graph the Tput over actions
df2 = pd.read_csv('./tmp/mm-vegas-iperfs-tput-trunc.csv')

# Iperf3 (mm), Iperf2 (mm)
colors = ['red', 'blue']

ax = df2.plot(style=['--','--'], color=colors, title='Network Congestion Control - Network Difference')
ax.set_ylabel('Throughput (Mbps)')
ax.set_xlabel('Time (ms)')

#plt.yticks(np.arange(6, 18, step=2))
plt.xticks(np.arange(0.0, 1300, step=100))
plt.savefig('./tmp/benchmark-throughput-between-application-configs-mm-iperfs.png')
plt.close()

# load the iperf3 Jsons
# load the iperf2 txts

# Iperf3 (mm), Iperf2 (mm), Iperf3(mn), Iperf2(mn)
colors = ['red', 'blue', 'green','brown']