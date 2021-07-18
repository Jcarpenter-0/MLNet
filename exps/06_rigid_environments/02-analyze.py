import subprocess
import matplotlib.pyplot as plt
import json
import glob
import numpy as np
import pandas as pd
import scipy.stats
from scipy import stats
import math
from sklearn import preprocessing

plt.style.use('seaborn-whitegrid')


def tscore(sample1, sample2) -> float:
    t2, p2 = stats.ttest_ind(sample1, sample2)
    return p2


def zscore(sample1, sample2) -> float:
    return -1


def CreateAnalysis(data1:pd.DataFrame, data2:pd.DataFrame, label:str, data1Label:str, data2Label:str):

    # Graph a boxplot
    # Adjust the values so the comparisons are in the same scale

    normalize=True

    if normalize:
        normData1 = pd.DataFrame(preprocessing.normalize(X=data1, axis=0), columns=data1.columns)
        normData2 = pd.DataFrame(preprocessing.normalize(X=data2, axis=0), columns=data2.columns)
    else:
        normData1 = data1
        normData2 = data2


    statFP = open('./tmp/{}-stat-analysis.txt'.format(label), 'w')

    for col in data1.columns:

        subNormData1 = normData1[col]
        subNormData2 = normData2[col]

        tpNormValue = tscore(subNormData1, subNormData2)
        zpNormValue = zscore(subNormData1, subNormData2)

        tpValue = tscore(data1[col], data2[col])
        zpValue = zscore(data1[col], data2[col])

        statFP.write('{} : tp={}\n'.format(col, tpValue))

        print('{}: {} - norm-tp:{} norm-zp:{} - tp:{} zp:{}'.format(label, col, tpNormValue, zpNormValue, tpValue, zpValue))

    combinedDF = pd.DataFrame()

    for col in data1.columns:
        combinedDF[data1Label + ' ' + col] = normData1[col]
        combinedDF[data2Label + ' ' + col] = normData2[col]

    statFP.flush()
    statFP.close()

    combinedDF.to_csv('./tmp/{}.csv'.format(label), index=False)

    ax = combinedDF.boxplot(figsize=(2.5 * len(combinedDF.columns), 7), fontsize=16)
    if normalize:
        ax.set_ylabel('Normalized Metric Value', fontsize=16)
    else:
        ax.set_ylabel('Metric Value', fontsize=16)

    ax.set_xlabel('Metrics', fontsize=16)
    plt.title('Metric Comparison {}'.format(label), fontsize=16)

    if False:
        plt.show()
    else:
        plt.savefig('./tmp/metric-boxplots-{}.jpg'.format(label))

    plt.close()


def ProcessIperfExperiment(dataDir:str):
    # Iperf Files
    iperfFiles = glob.glob('{}Traces/*-iperf-*.csv'.format(dataDir))

    iperf3Files = glob.glob('{}Traces/*-iperf3-*.csv'.format(dataDir))

    # Get macro stats, distributions of each run's average throughput, average bps, and sums of both
    iperfAvgRewds = []
    iperfSumRewds = []
    iperfAvgBytes = []
    iperfAvgTputs = []
    iperfSumBytes = []
    iperfSumTputs = []

    mainIperfDF = pd.DataFrame()

    for iperfFile in iperfFiles:
        iperfDF = pd.read_csv(iperfFile)

        iperfAvgRewds.append(iperfDF['Reward'].mean())
        iperfSumRewds.append(iperfDF['Reward'].sum())

        iperfAvgBytes.append(iperfDF['transferred_bytes'].mean())
        iperfAvgTputs.append(iperfDF['bits_per_second'].mean())

        iperfSumBytes.append(iperfDF['transferred_bytes'].sum())
        iperfSumTputs.append(iperfDF['bits_per_second'].sum())

    iperf3AvgRewds = []
    iperf3SumRewds = []
    iperf3AvgBytes = []
    iperf3AvgTputs = []
    iperf3SumBytes = []
    iperf3SumTputs = []

    for iperfFile in iperf3Files:
        iperfDF = pd.read_csv(iperfFile)

        iperf3AvgRewds.append(iperfDF['Reward'].mean())
        iperf3SumRewds.append(iperfDF['Reward'].sum())

        iperf3AvgBytes.append(iperfDF['receiver-bytes'].mean())
        iperf3AvgTputs.append(iperfDF['receiver-bps'].mean())

        iperf3SumBytes.append(iperfDF['receiver-bytes'].sum())
        iperf3SumTputs.append(iperfDF['receiver-bps'].sum())

    #mainIperfDF['Avg Reward'] = iperfAvgRewds
    #mainIperfDF['Sum Reward'] = iperfSumRewds
    mainIperfDF['Avg Tput'] = iperfAvgTputs
    mainIperfDF['Avg Bytes'] = iperfAvgBytes
    #mainIperfDF['Sum Bytes'] = iperfSumBytes

    mainIperf3DF = pd.DataFrame()

    #mainIperf3DF['Avg Reward'] = iperf3AvgRewds
    #mainIperf3DF['Sum Reward'] = iperf3SumRewds
    mainIperf3DF['Avg Tput'] = iperf3AvgTputs
    mainIperf3DF['Avg Bytes'] = iperf3AvgBytes
    #mainIperf3DF['Sum Bytes'] = iperf3SumBytes

    return mainIperfDF, mainIperf3DF


def ProcessAbrExperiment(dataDir:str):

    chromeFiles = glob.glob('{}Traces/*-chrome-testing-*.csv'.format(dataDir))

    firefoxFiles = glob.glob('{}Traces/*-firefox-testing-*.csv'.format(dataDir))

    # Get macro stats, distributions of each run's average throughput, average bps, and sums of both
    chromeAvgRewards = []
    chromeSumRewards = []
    chromeAvgBuffer = []
    chromeAvgRebuffer = []
    chromeAvgBandwidthEstimate = []
    chromeAvgLastQuality = []

    for file in chromeFiles:
        df = pd.read_csv(file)

        chromeAvgRewards.append(df['Reward'].mean())
        chromeSumRewards.append(df['Reward'].sum())
        chromeAvgBuffer.append(df['buffer'].mean())
        chromeAvgRebuffer.append(df['RebufferTime'].mean())
        chromeAvgBandwidthEstimate.append(df['bandwidthEst'].mean())
        chromeAvgLastQuality.append(df['lastquality'].mean())

    firefoxAvgRewards = []
    firefoxSumRewards = []
    firefoxAvgBuffer = []
    firefoxAvgRebuffer = []
    firefoxAvgBandwidthEstimate = []
    firefoxAvgLastQuality = []

    for file in firefoxFiles:
        df = pd.read_csv(file)

        firefoxAvgRewards.append(df['Reward'].mean())
        firefoxSumRewards.append(df['Reward'].sum())
        firefoxAvgBuffer.append(df['buffer'].mean())
        firefoxAvgRebuffer.append(df['RebufferTime'].mean())
        firefoxAvgBandwidthEstimate.append(df['bandwidthEst'].mean())
        firefoxAvgLastQuality.append(df['lastquality'].mean())

    chromeDF = pd.DataFrame()
    firefoxDF = pd.DataFrame()

    chromeDF['Avg Reward'] = chromeAvgRewards
    firefoxDF['Avg Reward'] = firefoxAvgRewards

    chromeDF['Avg Bandwidth Est'] = chromeAvgBandwidthEstimate
    firefoxDF['Avg Bandwidth Est'] = firefoxAvgBandwidthEstimate

    chromeDF['Avg Last Quality'] = chromeAvgLastQuality
    firefoxDF['Avg Last Quality'] = firefoxAvgLastQuality

    #chromeDF['Sum Reward'] = chromeSumRewards
    #firefoxDF['Sum Reward'] = firefoxSumRewards

    # macroDF['Chrome-Avg Buffer'] = chromeAvgBuffer
    # acroDF['Firefox-Avg Buffer'] = firefoxAvgBuffer

    chromeDF['Avg Rebuffer'] = chromeAvgRebuffer
    firefoxDF['Avg Rebuffer'] = firefoxAvgRebuffer

    return firefoxDF, chromeDF


# Metric Differences (pre-fix), boxplot of distributions, t-test, z-test

# Iperf vs Iperf3 (application difference)
iperfNaiveDF, iperf3NaiveDF = ProcessIperfExperiment('./../../../MLNet-Results/exp-05/tmp-p1/learner-application-dif/learner/')

CreateAnalysis(iperfNaiveDF, iperf3NaiveDF, 'Iperf vs Iperf3 (Application Dimension)', 'iperf', 'iperf3')

# Iperf vs Iperf3 running Parallels (application config difference)
iperfP4NaiveDF, iperf3P4NaiveDF = ProcessIperfExperiment('./../../../MLNet-Results/exp-05/tmp-p4/learner-application-dif/learner/')

CreateAnalysis(iperfNaiveDF, iperf3P4NaiveDF, 'Iperf vs Iperf3 Parallel TCPs (Application Dimension)', 'iperf', 'iperf3')


# Chrome vs Firefox (application difference)
abrFirefoxDF, abrChromeDF = ProcessAbrExperiment('./../../../MLNet-Results/exp-05/tmp-abr/learner/')

CreateAnalysis(abrFirefoxDF, abrChromeDF, 'Chrome vs Firefox ABR (Application Dimension)', 'Firefox', 'Chrome')


# 0 to m agents (multi-agent difference)


# Metric Differences (post-fix)

# Iperf vs Iperf3 (application difference)
iperfSoltuDF, iperf3SoltuDF = ProcessIperfExperiment('./../../../MLNet-Results/exp-05/tmp-p1-solution/learner-application-dif/learner/')

CreateAnalysis(iperfSoltuDF, iperf3SoltuDF, 'Iperf vs Iperf3 (expanded training)', 'iperf', 'iperf3')

CreateAnalysis(iperfNaiveDF, iperfSoltuDF, 'Iperf (pre vs post expanded training)', 'basic', 'expanded')

CreateAnalysis(iperf3NaiveDF, iperf3SoltuDF, 'Iperf3 (pre vs post expanded training)', 'basic', 'expanded')


# Iperf vs Iperf3 running Parallels (application config difference)
iperfP4SolutDF, iperf3P4SolutDF = ProcessIperfExperiment('./../../../MLNet-Results/exp-05/tmp-p4-solution/learner-application-dif/learner/')

CreateAnalysis(iperfP4SolutDF, iperf3P4SolutDF, 'Iperf vs Iperf3 Parallel TCPs (expanded training)', 'iperf', 'iperf3')

CreateAnalysis(iperfP4NaiveDF, iperfP4SolutDF, 'Iperf (pre vs post expanded training) Parallel TCPs', 'basic', 'expanded')

CreateAnalysis(iperf3P4NaiveDF, iperf3P4SolutDF, 'Iperf3 (pre vs post expanded training) Parallel TCPs', 'basic', 'expanded')


# Chrome vs Firefox (application difference)
abrFirefoxSoluDF, abrChromeSoluDF = ProcessAbrExperiment('./../../../MLNet-Results/exp-05/tmp-abr-solution/learner/')

CreateAnalysis(abrFirefoxSoluDF, abrChromeSoluDF, 'Chrome vs Firefox ABR (expanded training)', 'Firefox', 'Chrome')


# 0 to m agents (multi-agent difference)


