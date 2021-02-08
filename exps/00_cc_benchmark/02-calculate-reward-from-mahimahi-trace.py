DirOffset = ''
if __name__ == '__main__':
    # Setup the dir
    DirOffset = '../../'

    import os
    import sys
    sys.path.insert(0, os.getcwd())
    sys.path.insert(0, DirOffset)

import pandas as pd
import math
import numpy as np


dataDF = pd.read_csv('./tmp/mm-vegas-iperf3-up-log-trunc.csv')

observedMinRTT = 0x3fffffff
oldObservation = None


def getReward(obs):
    # copa's utility function: log(throughput) - delta * log(delay)

    delta = 0.5

    tput = obs['bytes']

    delay = obs['delay(ms)'] - observedMinRTT
    delay = delay if delay > 0 else 0

    logtput = math.log2(tput) if tput > 0 else 0
    logdelay = math.log2(delay) if delay > 0 else 0

    return (logtput - (delta * logdelay))


# group every n numbers into groups then get the average of them
rewards = []

groupSize = 10
groupAverages = []
group = []
count = 0

for row in dataDF.iterrows():

    row = row[1]

    if row['delay(ms)'] < observedMinRTT:
        observedMinRTT = row['delay(ms)']

    reward = 0

    if oldObservation is not None:
        reward = getReward(oldObservation)

    rewards.append(reward)

    oldObservation = row

    # handle the grouping
    count += 1

    if count <= groupSize:
        # add to group
        group.append(reward)
    else:
        # add to next group
        groupAverages.append(np.mean(group))
        group = [reward]
        count = 0

if count > 0:
    # deal with rest
    groupAverages.append(np.mean(group))

print('Ready for DF')
rewardsAggDf = pd.DataFrame(columns=['Reward'], data=rewards)
rewardsAggDf.to_csv('./tmp/reward-only.csv'.format(), index=None)

rewardGroupedDF = pd.DataFrame(columns=['Reward'], data=groupAverages)
rewardGroupedDF.to_csv('./tmp/reward-only-group-{}.csv'.format(groupSize), index=None)