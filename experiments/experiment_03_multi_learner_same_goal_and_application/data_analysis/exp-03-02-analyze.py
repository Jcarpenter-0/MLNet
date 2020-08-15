import pandas as pd
import numpy as np
import glob
import json

RESULTDIR = '../tmp-02/'

Environments = [
    'env-mm-delay-0',
    'env-mm-delay-50',
    'env-mm-delay-100',
    'env-mm-delay-150',
    'env-mm-loss-uplink-0.0',
    'env-mm-loss-uplink-0.1'
]

def ParseTraceFiles():


    results = []

    learners = glob.glob(RESULTDIR + '*')

    # for each learner
    for learner in learners:

        learnerRow = pd.DataFrame()

        learnerRow['Learner'] = [learner]

        # for each trace file, group together by environment
        for env in Environments:

            testenvRewardSum = 0
            testenvRewardNormSum = 0
            testenvStepCount = 0

            testTraceFiles = glob.glob(learner + '/traces/*-tst-{}-testing-runlogs.csv'.format(env))

            for traceFile in testTraceFiles:
                traceDF = pd.read_csv(traceFile)

                testenvRewardSum += traceDF['Reward'].sum()
                testenvRewardNormSum += traceDF['Normalized-Reward'].sum()
                testenvStepCount += traceDF.shape[0]

            learnerRow['tst-{}-Reward-Sum'.format(env)] = [testenvRewardSum]
            learnerRow['tst-{}-Reward-Norm-Sum'.format(env)] = [testenvRewardNormSum]
            learnerRow['tst-{}-Step-Count'.format(env)] = [testenvStepCount]

            verfTraceFiles = glob.glob(learner + '/traces/*-tst-{}-validation-runlogs.csv'.format(env))

            for idx, traceFile in enumerate(verfTraceFiles):
                traceDF = pd.read_csv(traceFile)

                verfenvRewardSum = 0
                verfenvRewardNormSum = 0
                verfenvStepCount = 0

                verfenvRewardSum += traceDF['Reward'].sum()
                verfenvRewardNormSum += traceDF['Normalized-Reward'].sum()
                verfenvStepCount += traceDF.shape[0]

                learnerRow['vrf-{}-{}-Reward-Sum'.format(idx, env)] = [verfenvRewardSum]
                learnerRow['vrf-{}-{}-Reward-Norm-Sum'.format(idx,env)] = [verfenvRewardNormSum]
                learnerRow['vrf-{}-{}-Step-Count'.format(idx,env)] = [verfenvStepCount]

        results.append(learnerRow)
        print('{} - Completed'.format(learner))

    returnDF = results[0]

    for row in results[1:]:
        returnDF = returnDF.append(row)


    return returnDF


if __name__ == '__main__':
    result = ParseTraceFiles()
    result.to_csv('./exp-03-02-analysis.csv', index=False)
    print('Done')