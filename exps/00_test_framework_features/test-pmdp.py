# =====================================
# Demonstrate the partially defined Markovian Decision Process feature
# =====================================

# Setup the dir
DirOffset = '../../'

import os
import sys

sys.path.insert(0, os.getcwd())
sys.path.insert(0, DirOffset)

import pandas as pd
import mdp

mdpList = list()

upperBound = 242.0
lowerBound = 241.0

# Low
mdpList.append(mdp.State([lambda x: x['rttAvg'] >= upperBound or x['packetLoss'] > 0]))
# Ambiguous
mdpList.append(mdp.State([lambda x: x['rttAvg'] < upperBound and x['rttAvg'] > lowerBound]))
# High
mdpList.append(mdp.State([lambda x: x['rttAvg'] <= lowerBound or x['packetLoss'] == 0]))

dataDF = pd.read_csv('exps/0X_ping_example/tmp/Traces/07-12-2020-13-47-11-trn-1-session-log.csv')

_, dataDF['state-id'] = mdp.AnalyzeTrace(dataDF, mdpList)

print(dataDF.head())
