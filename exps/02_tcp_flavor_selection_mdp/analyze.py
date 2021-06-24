import glob
import pandas as pd
import matplotlib.pyplot as plt
import numpy as np
import sys

plt.style.use('seaborn-whitegrid')

benchmarkInputDir = sys.argv[1]

naiveInputDir = sys.argv[2]

constrainedInputDir = sys.argv[3]

mdpInputDir = sys.argv[4]

# Graph 1, reward over actions
dataFiles = glob.glob(benchmarkInputDir + '*.csv')

combinedDF = pd.DataFrame()

for file in dataFiles:

    df2 = pd.read_csv(file)

    benchmarkName = file.split('/')[-1].split('.')[0]

    combinedDF[benchmarkName] = df2['Reward']

colors = ['red', 'green', 'blue', 'orange', 'yellow','brown', 'purple']


ax = combinedDF.plot(style=['--', '--', '--', '--', '--', '--', '--'], color=colors, title='Network Congestion Control - MDP Benchmark', figsize=(25, 11))
ax.set_ylabel('Reward')
ax.set_xlabel('Number of Actions (10s)')

plt.yticks(np.arange(12, 34, step=2))
plt.xticks(np.arange(0.0, 370, step=30))
plt.savefig('./tmp/benchmark-reward-between-ccs.png')
plt.close()

# Graph 2, mdp learner vs naive learner
combinedDF = pd.DataFrame()

colors = ['blue', 'green', 'red']

naiveDF = pd.read_csv(glob.glob(naiveInputDir + '*.csv')[0])

constrainedDF = pd.read_csv(glob.glob(constrainedInputDir + '*.csv')[0])

mdpDF = pd.read_csv(glob.glob(mdpInputDir + '*.csv')[0])

combinedDF['naive'] = naiveDF['Reward']
combinedDF['mdp'] = mdpDF['Reward']
combinedDF['constrained'] = constrainedDF['Reward']

ax = combinedDF.plot(style=['--'], color=colors, title='Network Congestion Control - MDP', figsize=(25, 11))
ax.set_ylabel('Reward')
ax.set_xlabel('Number of Actions (10s)')

plt.yticks(np.arange(12, 34, step=2))
plt.xticks(np.arange(0.0, 370, step=30))
plt.savefig('./tmp/mdp-naive-constrained-reward.png')
plt.close()