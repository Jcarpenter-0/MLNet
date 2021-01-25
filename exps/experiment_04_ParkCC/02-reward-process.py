DirOffset = ''
if __name__ == '__main__':
    # Setup the dir
    DirOffset = '../../'

    import os
    import sys
    sys.path.insert(0, os.getcwd())
    sys.path.insert(0, DirOffset)

import pandas as pd
import networks.mahimahi
import math


dataDF = pd.read_csv('./data/up-log.csv')

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

for row in dataDF.iterrows():

    row = row[1]

    if row['delay(ms)'] < observedMinRTT:
        observedMinRTT = row['delay(ms)']

    if oldObservation is not None:
        rewards.append(getReward(oldObservation))
    else:
        rewards.append(0)

    oldObservation = row

print('Ready for DF')
rewardsAggDf = pd.DataFrame(columns=['Reward'], data=rewards)

rewardsAggDf.to_csv('./data/reward-only-groups.csv'.format(), index=None)
