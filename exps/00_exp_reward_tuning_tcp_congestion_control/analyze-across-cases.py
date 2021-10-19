import pandas as pd
import numpy as np
import glob
import matplotlib.pyplot as plt

agentCountsToGraph = [1, 2, 4]
percentsToGraph = [25, 50, 75]

filterDownTo = None
aggregateBy = None

# Graph the qualities between approaches
qualitiesData = pd.DataFrame()

# Graph the "steering capacity"
topLevelQualityValues = []
topLevelFairnessValues = []
topLevelTemporalValues = []

for percentFairness in percentsToGraph:

    subData = pd.DataFrame()
    # each of these is runs
    # quality values taken from each "run"
    qualityValues = []
    fairnessValues = []
    temporalValues = []

    for agentCount in agentCountsToGraph:

        dataDirs = glob.glob('./tmp-{}-agent-{}p/domain/*.csv'.format(agentCount, percentFairness))

        for dataFile in dataDirs:
            dataFileDF = pd.read_csv(dataFile)

            qualityValues.append(dataFileDF['lastquality'].mean())
            fairnessValues.append(dataFileDF['fairness'].mean())
            temporalValues.append(dataFileDF['chunk-download-time-millisecond'].mean())

    topLevelQualityValues.append(np.mean(qualityValues))
    topLevelFairnessValues.append(np.mean(fairnessValues))
    topLevelTemporalValues.append(np.mean(temporalValues))

steeringDataGraph1 = pd.DataFrame()
steeringDataGraph1['Fairness-Weight'] = percentsToGraph
steeringDataGraph1['Data-Consumed'] = topLevelQualityValues
steeringDataGraph1['Fairness'] = topLevelFairnessValues
steeringDataGraph1['Temporal'] = topLevelTemporalValues

pass