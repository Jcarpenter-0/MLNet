import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

plt.style.use('seaborn-whitegrid')

# Graph the Reward vs Actions for mm and Iperfs
df2 = pd.read_csv('./results/Config-Results/mm-vegas-iperfs-trunc-reward-only-group-10.csv')

# Iperf3, Iperf2
colors = ['red', 'green']

ax = df2.plot(style=['--','--'], color=colors, title='Network Congestion Control - Application Difference')
ax.set_ylabel('Reward')
ax.set_xlabel('Number of Actions (10ms)')

plt.yticks(np.arange(6, 18, step=2))
plt.xticks(np.arange(0.0, 1200, step=100))
plt.savefig('./results/benchmark-reward-between-application-configs-mm-iperfs.jpg')
plt.close()

# Graph the Tput over actions
df2 = pd.read_csv('./results/Config-Results/mm-vegas-iperfs-up-log-trunc.csv')

# Iperf3, Iperf2
colors = ['red', 'blue', 'green','brown']

ax = df2.plot(style=['--','--','--','--'], color=colors, title='Network Congestion Control - Application Difference')
ax.set_ylabel('Throughput (Mbps)')
ax.set_xlabel('Time (ms)')

#plt.yticks(np.arange(6, 18, step=2))
#plt.xticks(np.arange(0.0, 1200, step=100))
plt.savefig('./results/benchmark-throughput-between-application-configs-mm-iperfs.jpg')