import pandas as pd
import numpy as np
import glob

DirOffset = ''
if __name__ == '__main__':
    # Setup the dir
    DirOffset = '../../'

    import os
    import sys
    sys.path.insert(0, os.getcwd())
    sys.path.insert(0, DirOffset)

import tools


dataDirs = glob.glob('./tmp/*/')

seperationCriteria = 'agents-2'

combinedDF = pd.DataFrame()
bigCombinedDF = pd.DataFrame()

totalDFs = []
labels = []

for dataDir in dataDirs:
    approachName = dataDir.split('/')[-2]

    labels.append(approachName)

    # get data files
    dataFiles = glob.glob(dataDir + '*{}*.csv'.format(seperationCriteria))

    fairnesses = []
    lastQualities = []
    rewards = []

    for dataFile in dataFiles:
        data = pd.read_csv(dataFile)

        fairnesses.extend(data['fairness'].values)
        lastQualities.extend(data['lastquality'].values)
        rewards.extend(data['Reward'].values)

    fullDF = pd.DataFrame()

    # Just trimmers
    fairnesses = fairnesses[:7791]
    lastQualities = lastQualities[:7791]
    rewards = rewards[:7791]

    fullDF['Quality'] = lastQualities
    #fullDF['Fairness'] = fairnesses

    totalDFs.append(fullDF)

    bigCombinedDF[approachName + '-Quality'] = lastQualities[:7791]
    bigCombinedDF[approachName + '-Fairness'] = fairnesses[:7791]

    #combinedDF[approachName + '-avgReward'] = [np.average(rewards)]
    combinedDF[approachName + '-avgFairness'] = [np.average(fairnesses)]
    combinedDF[approachName + '-avgQuality'] = [np.average(lastQualities)]
    combinedDF[approachName + '-sampleSize'] = [len(rewards)]
    #combinedDF[approachName + '-stdFairness'] = [np.std(fairnesses)]
    #combinedDF[approachName + '-stdQuality'] = [np.std(lastQualities)]


combinedDF.to_csv('./tmp/report.csv', index=False)

tools.CreateAnalysis(totalDFs[0], totalDFs[1], '{}-{}'.format(labels[0], labels[1]), labels[0], labels[1], normalize=False, groupSamples=250)

#tools.CreateGroupedGraph(bigCombinedDF, "combined-lines", normalize=False, groupSamples=250)
