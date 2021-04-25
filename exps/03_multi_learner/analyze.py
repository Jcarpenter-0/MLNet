import glob
import pandas as pd
import matplotlib.pyplot as plt
import numpy as np

plt.style.use('seaborn-whitegrid')

singleBenchmarkDF = pd.read_csv(glob.glob('./tmp/one-benchmark/learner/Traces/*-vegas-*.csv')[0])

duoBenchmark1DF = pd.read_csv(glob.glob('./tmp/benchmark1/learner/Traces/*-vegas-*.csv')[0])
duoBenchmark2DF = pd.read_csv(glob.glob('./tmp/benchmark2/learner/Traces/*-vegas-*.csv')[0])

# Graph 1, Benchmarks
combinedDF = pd.DataFrame()

combinedDF['Solo-Vegas'] = singleBenchmarkDF['Reward']
combinedDF['Duo-1-Vegas'] = duoBenchmark1DF['Reward']
combinedDF['Duo-2-Vegas'] = duoBenchmark2DF['Reward']

colors = ['red', 'green', 'blue']

ax = combinedDF.plot(style=['--', '--', '--'], color=colors, title='Multi-Agent - Benchmark', figsize=(25, 11))
ax.set_ylabel('Reward')
ax.set_xlabel('Number of Actions (10s)')

plt.yticks(np.arange(12, 34, step=2))
plt.xticks(np.arange(0.0, 370, step=30))
plt.savefig('./tmp/multi-benchmark.png')
plt.close()

# Graph 2, Learners
singleLearner = pd.read_csv(glob.glob('./tmp/one-learner/learner/Traces/*--session-log.csv')[0])

duoLearner1DF = pd.read_csv(glob.glob('./tmp/learner1/learner/Traces/*.csv')[0])
duoLearner2DF = pd.read_csv(glob.glob('./tmp/learner2/learner/Traces/*.csv')[0])

combinedDF = pd.DataFrame()

combinedDF['Solo-learner'] = singleLearner['Reward']
combinedDF['Duo-1-learner'] = duoLearner1DF['Reward']
combinedDF['Duo-2-learner'] = duoLearner2DF['Reward']

colors = ['red', 'green', 'blue']

ax = combinedDF.plot(style=['--', '--', '--'], color=colors, title='Multi-Agent - Learners', figsize=(25, 11))
ax.set_ylabel('Reward')
ax.set_xlabel('Number of Actions (10s)')

plt.yticks(np.arange(12, 34, step=2))
plt.xticks(np.arange(0.0, 370, step=30))
plt.savefig('./tmp/multi-learner.png')
plt.close()

# Graph 3 in alternative enviromnet
soloDuo1 = pd.read_csv(glob.glob('./tmp/one-learner/learner/Traces/*--solo-duo-session-log.csv')[0])
soloDuo2 = pd.read_csv(glob.glob('./tmp/one-learner-2/learner/Traces/*--solo-duo-session-log.csv')[0])


combinedDF = pd.DataFrame()

combinedDF['soloDuo1-learner'] = soloDuo1['Reward']
combinedDF['soloDuo2-learner'] = soloDuo2['Reward']

colors = ['red', 'green']

ax = combinedDF.plot(style=['--', '--'], color=colors, title='Multi-Agent - Solo in Shared', figsize=(25, 11))
ax.set_ylabel('Reward')
ax.set_xlabel('Number of Actions (10s)')

plt.yticks(np.arange(12, 34, step=2))
plt.xticks(np.arange(0.0, 370, step=30))
plt.savefig('./tmp/solo-duo-learner.png')
plt.close()

# Generate data table
analysisTable = pd.DataFrame()

singleBenchmarkDF = pd.read_csv(glob.glob('./tmp/one-benchmark/learner/Traces/*-vegas-*.csv')[0])
duoBenchmark1DF = pd.read_csv(glob.glob('./tmp/benchmark1/learner/Traces/*-vegas-*.csv')[0])
duoBenchmark2DF = pd.read_csv(glob.glob('./tmp/benchmark2/learner/Traces/*-vegas-*.csv')[0])

singleLearner = pd.read_csv(glob.glob('./tmp/one-learner/learner/Traces/*--session-log.csv')[0])
duoLearner1DF = pd.read_csv(glob.glob('./tmp/learner1/learner/Traces/*.csv')[0])
duoLearner2DF = pd.read_csv(glob.glob('./tmp/learner2/learner/Traces/*.csv')[0])

soloDuo1 = pd.read_csv(glob.glob('./tmp/one-learner/learner/Traces/*--solo-duo-session-log.csv')[0])
soloDuo2 = pd.read_csv(glob.glob('./tmp/one-learner-2/learner/Traces/*--solo-duo-session-log.csv')[0])

analysisTable['Setup'] = ['Learner-Duo-1', 'Learner-Duo-2', 'Learner-Solo-Duo-1', 'Learner-Solo-Duo-2', 'Learner-Solo', 'Vegas-Duo-1', 'Vegas-Duo-2', 'Vegas-Solo']

analysisTable['Observed (bytes)'] = [
     duoLearner1DF['Raw-sender-bytes'].sum()
    , duoLearner2DF['Raw-sender-bytes'].sum()
    , soloDuo1['Raw-sender-bytes'].sum()
    , soloDuo2['Raw-sender-bytes'].sum()
    , singleLearner['Raw-sender-bytes'].sum()
    , duoBenchmark1DF['Raw-sender-bytes'].sum()
    , duoBenchmark2DF['Raw-sender-bytes'].sum()
    , singleBenchmarkDF['Raw-sender-bytes'].sum()
                                     ]

analysisTable['Expected (bytes)'] = [
    singleLearner['Raw-sender-bytes'].sum()/2
    , singleLearner['Raw-sender-bytes'].sum()/2
    , singleLearner['Raw-sender-bytes'].sum()/2
    , singleLearner['Raw-sender-bytes'].sum()/2
    , singleLearner['Raw-sender-bytes'].sum()
    , singleBenchmarkDF['Raw-sender-bytes'].sum()/2
    , singleBenchmarkDF['Raw-sender-bytes'].sum()/2
    , singleBenchmarkDF['Raw-sender-bytes'].sum()

]

analysisTable['Gap (bytes)'] = [
     duoLearner1DF['Raw-sender-bytes'].sum() - singleLearner['Raw-sender-bytes'].sum()/2
    , duoLearner2DF['Raw-sender-bytes'].sum() - singleLearner['Raw-sender-bytes'].sum()/2
    , soloDuo1['Raw-sender-bytes'].sum() - singleLearner['Raw-sender-bytes'].sum()/2
    , soloDuo2['Raw-sender-bytes'].sum() - singleLearner['Raw-sender-bytes'].sum()/2
    , 0
    , duoBenchmark1DF['Raw-sender-bytes'].sum() - singleBenchmarkDF['Raw-sender-bytes'].sum()/2
    , duoBenchmark2DF['Raw-sender-bytes'].sum() - singleBenchmarkDF['Raw-sender-bytes'].sum()/2
    , 0

]

analysisTable['Gap (percentage)'] = [
    (duoLearner1DF['Raw-sender-bytes'].sum() - singleLearner['Raw-sender-bytes'].sum() / 2)/singleLearner['Raw-sender-bytes'].sum()
    , (duoLearner2DF['Raw-sender-bytes'].sum() - singleLearner['Raw-sender-bytes'].sum() / 2)/singleLearner['Raw-sender-bytes'].sum()
    , (soloDuo1['Raw-sender-bytes'].sum() - singleLearner['Raw-sender-bytes'].sum() / 2)/singleLearner['Raw-sender-bytes'].sum()
    , (soloDuo2['Raw-sender-bytes'].sum() - singleLearner['Raw-sender-bytes'].sum() / 2)/singleLearner['Raw-sender-bytes'].sum()
    , 0
    , (duoBenchmark1DF['Raw-sender-bytes'].sum() - singleBenchmarkDF['Raw-sender-bytes'].sum() / 2)/singleBenchmarkDF['Raw-sender-bytes'].sum()
    , (duoBenchmark2DF['Raw-sender-bytes'].sum() - singleBenchmarkDF['Raw-sender-bytes'].sum() / 2)/singleBenchmarkDF['Raw-sender-bytes'].sum()
    , 0
]

analysisTable['Sum (bytes)'] = [
     duoLearner1DF['Raw-sender-bytes'].sum() + duoLearner2DF['Raw-sender-bytes'].sum()
    , 0
    , soloDuo1['Raw-sender-bytes'].sum() + soloDuo2['Raw-sender-bytes'].sum()
    , 0
    , singleLearner['Raw-sender-bytes'].sum()
    , duoBenchmark1DF['Raw-sender-bytes'].sum() + duoBenchmark2DF['Raw-sender-bytes'].sum()
    , 0
    , singleBenchmarkDF['Raw-sender-bytes'].sum()
]

analysisTable.to_csv('./tmp/data-table.csv', index=False)

# top level analyze on the multi-learner
multiLearnerRuns = glob.glob('tmp-*/data-table.csv')

# combine the multiple runs to establish variations
combinedMultiRunsDF = pd.DataFrame()

# get statistical data on each of the experiment runs data
learnerDuoGaps = []
learnerDuoSums = []
learnerSoloGaps = []
learnerSoloSums = []
vegasDuoGaps = []
vegasDuoSums = []

for multiRun in multiLearnerRuns:

    runDF = pd.read_csv(multiRun)

    # Learner duos
    ld1Gap = runDF[runDF['Setup'] == 'Learner-Duo-1']['Gap (percentage)'][0]
    ld1Sum = runDF[runDF['Setup'] == 'Learner-Duo-1']['Sum (bytes)'][0]

    learnerDuoGaps.append(ld1Gap)
    learnerDuoSums.append(ld1Sum)

    # Learner solos
    ls1Gap = runDF[runDF['Setup'] == 'Learner-Solo-Duo-1']['Gap (percentage)'][2]
    ls1Sum = runDF[runDF['Setup'] == 'Learner-Solo-Duo-1']['Sum (bytes)'][2]

    learnerSoloGaps.append(ls1Gap)
    learnerSoloSums.append(ls1Sum)

    # Vegas duos
    vd1Gap = runDF[runDF['Setup'] == 'Vegas-Duo-1']['Gap (percentage)'][5]
    vd1Sum = runDF[runDF['Setup'] == 'Vegas-Duo-1']['Sum (bytes)'][5]

    vegasDuoGaps.append(vd1Gap)
    vegasDuoSums.append(vd1Sum)

# Do the stat operations
ldGapSTD = np.std(learnerDuoGaps)
ldGapMean = np.mean(learnerDuoGaps)

lsGapSTD = np.std(learnerSoloGaps)
lsGapMean = np.mean(learnerSoloGaps)

vdGapSTD = np.std(vegasDuoGaps)
vdGapMean = np.mean(vegasDuoGaps)

gapsDF = pd.DataFrame()

gapsDF['Learner-Duo-Gap-STD'] = [ldGapSTD]
gapsDF['Learner-Solo-Gap-STD'] = [lsGapSTD]
gapsDF['Vegas-Duo-Gap-STD'] = [vdGapSTD]

gapsDF['Learner-Duo-Gap-Mean'] = [ldGapMean]
gapsDF['Learner-Solo-Gap-Mean'] = [lsGapMean]
gapsDF['Vegas-Duo-Gap-Mean'] = [vdGapMean]

gapsDF.to_csv('./tmp/multi-run-gaps.csv', index=None)

print()