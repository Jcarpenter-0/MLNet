import pandas as pd
import matplotlib.pyplot as plt
import numpy as np
import glob

# Reward Binning, just sum the rewards into groups
binSize = 1

# Graph 1 Benchmark Comparison
benchmarkDFBB = pd.read_csv(glob.glob('./tmp/BB-abr/Traces/*.csv')[0])

combinedDF = pd.DataFrame()

combinedDF['Buffer-Based'] = benchmarkDFBB['Reward']

rewardSums = []
runningSum = 0
runningBinCount = 1

for row in combinedDF.iterrows():

    rewardValue = row[1][0]

    runningSum += rewardValue * 100

    if runningBinCount == binSize:
        rewardSums.append(runningSum)
        runningBinCount = 1
        runningSum = 0
    else:
        runningBinCount += 1

# Get last bit
if runningBinCount > 1 and runningSum > 0:
    rewardSums.append(runningSum)

finalDF = pd.DataFrame()

finalDF['Buffer-Based'] = rewardSums

colors = ['red', 'green', 'blue']

ax = finalDF.plot(style=['--', '--', '--'], color=colors, title='ABR - Benchmark', figsize=(25, 11))
ax.set_ylabel('Reward')
ax.set_xlabel('Number of Actions (1e03')

plt.yticks(np.arange(-2000, 1500, step=500))
plt.xticks(np.arange(0, 140, step=5))
plt.savefig('./tmp/abr-benchmark.png')
plt.close()