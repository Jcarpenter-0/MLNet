# This script will take in a csv file, and create two files containing correlations between each csv column

import pandas as pd
from scipy.stats import pearsonr
from scipy.stats import spearmanr

# Useful Resources
# https://machinelearningmastery.com/how-to-use-correlation-to-understand-the-relationship-between-variables/
# https://en.wikipedia.org/wiki/Document-term_matrix

# Input Variables
INPUTFILEPATH = '../../exps/experiment_02_congestion_control_micro/tmp/cclearner/traces/09-07-2020-02-11-05-training-runlogs.csv'
INPUTFILENAME = INPUTFILEPATH.split('/')[-1]

macroDF = pd.read_csv(INPUTFILEPATH)

DROPFILTER = ['Timestamp', 'Reward', 'Exploit']

macroDF = macroDF.drop(columns=DROPFILTER)

metricLabels = macroDF.columns.values

# Output Variables
OUTPUTFILEPATH = './'
OUTPUTPOSTFIX = '.csv'
OUTPUTDELIMITER = ','

OUTPUTHEADER = 'Metrics' + OUTPUTDELIMITER

# build the header
for index, label in enumerate(metricLabels):
    OUTPUTHEADER = OUTPUTHEADER + label

    if index < len(metricLabels) - 1:
        OUTPUTHEADER = OUTPUTHEADER + OUTPUTDELIMITER

OUTPUTHEADER = OUTPUTHEADER + '\n'

# Structure (Adjacency Matrix, where coordinate values are correlations):
# XXXX, label1, label2, label3
# label1, N/A, 0.1, 1.0
# label2, 1.0, N/A, 0.8
# label3, 1.0, .88, N/A

AdjMatrixPearson = []
AdjMatrixSpearman = []

# For each metric, ...
for index, metricLabel in enumerate(metricLabels):
    metricValues = macroDF[metricLabel]

    metricDataType = metricValues.dtype

    # change the data type to numeric for correlations

    # skip if non-numeric
    if metricDataType.name != 'object':


        # hold the correlations here for adj row
        spearmanCorrelations = []
        pearsonCorrelations = []

        # ... against each other metric
        for compareMetricIndex, compareMetricLabel in enumerate(metricLabels):

            # skip if comparing to self, N/A case
            if compareMetricIndex != index:

                # get test data from macro data
                compareMetricValues = macroDF[compareMetricLabel]

                compareDataType = compareMetricValues.dtype

                # change data type to numeric to facilitate the correlations

                # or ignore non-numeric data
                if compareDataType.name != 'object':
                    print(metricLabel + ' ' + metricDataType.name + ' ' + compareMetricLabel + ' ' + compareDataType.name)
                    # Pearson can be applied to each variable to each other to form the two way correlation for linear relationship
                    corrPear, resMatrixPear = pearsonr(metricValues, compareMetricValues)

                    # Spearman for non-linear relationship or if you don't know
                    corrSpear, resMatrixSpear = spearmanr(metricValues, compareMetricValues)

                    spearmanCorrelations.append(corrSpear)
                    pearsonCorrelations.append(corrPear)

                    print(metricLabel + '-' + compareMetricLabel)
                    print('Pearson (Linear):' + str(corrPear))
                    print('Spearman (Non-Linear):' + str(corrSpear))
            else:
                spearmanCorrelations.append('N/A')
                pearsonCorrelations.append('N/A')

        # Append the row to the overall data structure
        AdjMatrixPearson.append(pearsonCorrelations)
        AdjMatrixSpearman.append(spearmanCorrelations)

# Write out the adjacency matrix
PearsonFileDS = open(OUTPUTFILEPATH + INPUTFILENAME + '_Pearson' + OUTPUTPOSTFIX, 'w')

# write header
PearsonFileDS.write(OUTPUTHEADER)

for index, row in enumerate(AdjMatrixPearson):

    valueString = ''

    for num, entry in enumerate(row):
        valueString = valueString + str(entry)

        if num < len(row)-1:
            valueString = valueString + OUTPUTDELIMITER

    PearsonFileDS.write(metricLabels[index] + OUTPUTDELIMITER + valueString + '\n')

PearsonFileDS.flush()
PearsonFileDS.close()

SpearmanFileDS = open(OUTPUTFILEPATH + INPUTFILENAME + '_Spearman' + OUTPUTPOSTFIX, 'w')

SpearmanFileDS.write(OUTPUTHEADER)

for index, row in enumerate(AdjMatrixSpearman):

    valueString = ''

    for num, entry in enumerate(row):
        valueString = valueString + str(entry)

        if num < len(row) - 1:
            valueString = valueString + OUTPUTDELIMITER

    SpearmanFileDS.write(metricLabels[index] + OUTPUTDELIMITER + valueString + '\n')

SpearmanFileDS.flush()
SpearmanFileDS.close()