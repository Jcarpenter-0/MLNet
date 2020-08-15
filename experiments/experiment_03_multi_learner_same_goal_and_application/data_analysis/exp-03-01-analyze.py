import pandas as pd
import numpy as np
import glob
import json

RESULTDIR = '../tmp-01/'

def ParseReports():

    # For each model,
    models = glob.glob(RESULTDIR + '*')

    for model in models:

        modelReport = glob.glob(model + '/*.json')[0]

        modelReportFD = open(modelReport, 'r')

        reportdata = json.load(modelReportFD)

        modelReportFD.close()

        # For each tracefile (that differs)
        testingSessions = reportdata['testing-sessions']

        groupingTraceName = None
        groupRewardSum = 0
        groupRewardSumNorm = 0
        groupTotalStepCount = 0

        for testingSession in testingSessions:

            traceNamePieces = testingSession['trace-file'].split('-')

            traceName = ''

            sessionRunLength = testingSession['runLengthInSteps']
            sessionRewardSum = 0
            sessionRewardNormSum = 0

            for action in testingSession['action-breakdown']:
                sessionRewardSum += action['sum']
                sessionRewardNormSum += action['nrm-sum']

            for index, piece in enumerate(traceNamePieces[-4:]):
                traceName += piece
                if index < len(traceNamePieces[-4:]):
                    traceName += '-'

            if groupingTraceName is None:
                groupingTraceName = traceName
            else:

                if traceName not in groupingTraceName:
                    # new grouping
                    groupingTraceName = traceName
                    groupRewardSum = 0
                    groupRewardSumNorm = 0
                    groupTotalStepCount = 0


        # Get the sum of rewards, run length (total)


def ParseTraces():

    results = []

    learnerRowTemplate = pd.DataFrame(columns=['Learner'
        , 'Testing-Together-Reward-Sum'
        , 'Testing-Separately-Reward-Sum'
        , 'Testing-Together-Reward-Norm-Sum'
        , 'Testing-Separately-Reward-Norm-Sum'
        , 'Testing-Together-Step-Count'
        , 'Testing-Separately-Step-Count'
        , 'Training-Together-Reward-Sum'
        , 'Training-Separately-Reward-Sum'
        , 'Training-Together-Reward-Norm-Sum'
        , 'Training-Separately-Reward-Norm-Sum'
        , 'Training-Together-Step-Count'
        , 'Training-Separately-Step-Count'
                                               ])

    # for each learner
    learners = glob.glob(RESULTDIR + '*')

    for learner in learners:

        learnerRow = learnerRowTemplate.copy()
        learnerRow['Learner'] = [learner]

        # get training data
        # for each testing trace in the learner subdir
        trainTogetherTraceFiles = glob.glob(learner + '/traces/*-trn-together-training-runlogs.csv')

        trainTogetherRewardSum = 0
        trainTogetherRewardNormSum = 0
        trainTogetherStepCount = 0

        for traceFile in trainTogetherTraceFiles:

            traceDF = pd.read_csv(traceFile)

            trainTogetherRewardSum += traceDF['Reward'].sum()
            trainTogetherRewardNormSum += traceDF['Normalized-Reward'].sum()
            trainTogetherStepCount += traceDF.shape[0]


        learnerRow['Training-Together-Reward-Sum'] = [trainTogetherRewardSum]
        learnerRow['Training-Together-Reward-Norm-Sum'] = [trainTogetherRewardNormSum]
        learnerRow['Training-Together-Step-Count'] = [trainTogetherStepCount]

        trainSeperateTraceFiles = glob.glob(learner + '/traces/*-trn-seperately-training-runlogs.csv')

        trainSeperateRewardSum = 0
        trainSeperateRewardNormSum = 0
        trainSeperateStepCount = 0

        for traceFile in trainSeperateTraceFiles:

            traceDF = pd.read_csv(traceFile)

            trainSeperateRewardSum += traceDF['Reward'].sum()
            trainSeperateRewardNormSum += traceDF['Normalized-Reward'].sum()
            trainSeperateStepCount += traceDF.shape[0]


        learnerRow['Training-Separately-Reward-Sum'] = [trainSeperateRewardSum]
        learnerRow['Training-Separately-Reward-Norm-Sum'] = [trainSeperateRewardNormSum]
        learnerRow['Training-Separately-Step-Count'] = [trainSeperateStepCount]


        # for each testing trace in the learner subdir
        testTogetherTraceFiles = glob.glob(learner + '/traces/*-tst-together-testing-runlogs.csv')
        testTogetherTraceFiles.extend(glob.glob(learner + '/traces/*-vrf-together-validation-runlogs.csv'))

        testTogetherRewardSum = 0
        testTogetherRewardNormSum = 0
        testTogetherStepCount = 0

        for traceFile in testTogetherTraceFiles:

            traceDF = pd.read_csv(traceFile)

            testTogetherRewardSum += traceDF['Reward'].sum()
            testTogetherRewardNormSum += traceDF['Normalized-Reward'].sum()
            testTogetherStepCount += traceDF.shape[0]


        learnerRow['Testing-Together-Reward-Sum'] = [testTogetherRewardSum]
        learnerRow['Testing-Together-Reward-Norm-Sum'] = [testTogetherRewardNormSum]
        learnerRow['Testing-Together-Step-Count'] = [testTogetherStepCount]

        # For other test case
        testSeperatelyTraceFiles = glob.glob(learner + '/traces/*-tst-seperate-testing-runlogs.csv')
        testSeperatelyTraceFiles.extend(glob.glob(learner + '/traces/*-vrf-seperate-validation-runlogs.csv'))

        testSeparatelyRewardSum = 0
        testSeparatelyRewardNormSum = 0
        testSeparatelyStepCount = 0

        for traceFile in testSeperatelyTraceFiles:

            traceDF = pd.read_csv(traceFile)

            testSeparatelyRewardSum += traceDF['Reward'].sum()
            testSeparatelyRewardNormSum += traceDF['Normalized-Reward'].sum()
            testSeparatelyStepCount += traceDF.shape[0]

        learnerRow['Testing-Separately-Reward-Sum'] = [testSeparatelyRewardSum]
        learnerRow['Testing-Separately-Reward-Norm-Sum'] = [testSeparatelyRewardNormSum]
        learnerRow['Testing-Separately-Step-Count'] = [testSeparatelyStepCount]

        results.append(learnerRow)
        print('{} - Completed'.format(learner))

    returnDF = results[0]

    for row in results[1:]:
        returnDF = returnDF.append(row)

    return returnDF

if __name__ == '__main__':
    result = ParseTraces()
    result.to_csv('./exp-03-01-analysis.csv', index=False)
    print('Done')