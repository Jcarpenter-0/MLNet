# Simple CC experiment, involving two nodes
import numpy as np

# Setup the dir
DirOffset = '../../'

import os
import sys
sys.path.insert(0, os.getcwd())
sys.path.insert(0, DirOffset)
import experiments.experiments_common


NumberOfLearners = 2
TrainingCount = 4
TestingCount = 6


ExperimentLengthSeconds = 1800

# Post-test cooldown
PostTestTimeBufferSecods = 10

# For other time estimations
ArbitraryTimeAddSeconds = 7

ValidationCount = 1
ValidationPatterns = [
    './cubic-pattern.csv',
    './bbr-pattern.csv',
    './vegas-pattern.csv',
    './reno-pattern.csv'
]

NetworkNodes = [
    ['mm-delay', '40', 'python3', DirOffset + 'applications/daemon_server.py', '8079'],
    ['python3', DirOffset + 'applications/daemon_server.py', '8079']
]

LearnerStartPort = 8080
ApplicationStartPort = LearnerStartPort + NumberOfLearners

LearnerName = 'congestion_control_manager'
LearnerLabel = 'exp-03-01-{}-{}'
LearnerLogPrefix = '{}'

# Number of iperf runs to attempt
IperfRuns = 1000

# How long the iperf runs should attempt to go for
IperfRunLengthSeconds = 10

# ===================================================================================

TestCount = (TrainingCount * 2) + (TestingCount * 4) + (ValidationCount * len(ValidationPatterns) * 2)
TestTimeEstimate = TestCount * (ExperimentLengthSeconds + ArbitraryTimeAddSeconds + PostTestTimeBufferSecods)
print('Tests planned {} - Time ~{} hours'.format(TestCount, (TestTimeEstimate / 60 / 60)))
input("Press Enter to continue... or ctrl-c to stop")

try:

    # Train together
    learnerLabel = 'trn-together'
    for index in range(0, TrainingCount):

        # setup learners
        learners = []

        # setup applications
        applications = []

        for learnerNum in range(0, NumberOfLearners):

            singleUseLearnerConfig = [(LearnerName, '{}'.format(LearnerStartPort + learnerNum), '', '1', LearnerLabel.format(learnerNum, learnerLabel), learnerLabel, '')]

            learners.extend(singleUseLearnerConfig.copy())

            singleUseAppCommand = [
                ('http://100.64.0.2:8079',
                 ['python3', DirOffset + 'applications/Iperf/experiment_02_congestion_control_micro/iperf_stub.py',
                  '-c',
                  '100.64.0.1', '-t', '10', '-p', '{}'.format(ApplicationStartPort + learnerNum), '1000',
                  'http://100.64.0.1:{}'.format(LearnerStartPort + learnerNum)])
                , ('http://localhost:8079', ['iperf3', '-s', '-p', '{}'.format(ApplicationStartPort + learnerNum)])
            ]

            applications.extend(singleUseAppCommand.copy())

        experiments.experiments_common.runExperiment(NetworkNodes, learners, applications, ExperimentLengthSeconds, PostTestTimeBufferSecods, PostTestTimeBufferSecods, DirOffset, True)

    # Test together
    traceLabel = 'tst-together'
    for index in range(0, TestingCount):

        # setup learners
        learners = []

        # setup applications
        applications = []

        for learnerNum in range(0, NumberOfLearners):

            singleUseLearnerConfig = [(LearnerName, '{}'.format(LearnerStartPort + learnerNum), '', '0', LearnerLabel.format(learnerNum, learnerLabel), traceLabel, '')]

            learners.extend(singleUseLearnerConfig.copy())

            singleUseAppCommand = [
                ('http://100.64.0.2:8079',
                 ['python3', DirOffset + 'applications/Iperf/experiment_02_congestion_control_micro/iperf_stub.py',
                  '-c',
                  '100.64.0.1', '-t', '10', '-p', '{}'.format(ApplicationStartPort + learnerNum), '1000',
                  'http://100.64.0.1:{}'.format(LearnerStartPort + learnerNum)])
                , ('http://localhost:8079', ['iperf3', '-s', '-p', '{}'.format(ApplicationStartPort + learnerNum)])
            ]

            applications.extend(singleUseAppCommand.copy())

        experiments.experiments_common.runExperiment(NetworkNodes, learners, applications, ExperimentLengthSeconds, PostTestTimeBufferSecods, PostTestTimeBufferSecods, DirOffset, True)

    # Test seperately
    traceLabel = 'tst-seperate'
    for index in range(0, TestingCount):

        for learnerNum in range(0, NumberOfLearners):
            singleUseLearnerConfig = [(LearnerName, '{}'.format(LearnerStartPort + learnerNum), '', '0',
                                       LearnerLabel.format(learnerNum, learnerLabel), traceLabel, '')]

            singleUseAppCommand = [
                ('http://100.64.0.2:8079',
                 ['python3', DirOffset + 'applications/Iperf/experiment_02_congestion_control_micro/iperf_stub.py',
                  '-c',
                  '100.64.0.1', '-t', '10', '-p', '{}'.format(ApplicationStartPort + learnerNum), '1000',
                  'http://100.64.0.1:{}'.format(LearnerStartPort + learnerNum)])
                , ('http://localhost:8079', ['iperf3', '-s', '-p', '{}'.format(ApplicationStartPort + learnerNum)])
            ]

            experiments.experiments_common.runExperiment(NetworkNodes, singleUseLearnerConfig, singleUseAppCommand, ExperimentLengthSeconds,
                                                     PostTestTimeBufferSecods, PostTestTimeBufferSecods, DirOffset,
                                                     True)

    # Train seperately
    learnerLabel = 'trn-seperately'
    for index in range(0, TrainingCount):

        for learnerNum in range(0, NumberOfLearners):
            singleUseLearnerConfig = [(LearnerName, '{}'.format(LearnerStartPort + learnerNum), '', '1',
                                       LearnerLabel.format(learnerNum, learnerLabel), learnerLabel, '')]

            singleUseAppCommand = [
                ('http://100.64.0.2:8079',
                 ['python3', DirOffset + 'applications/Iperf/experiment_02_congestion_control_micro/iperf_stub.py',
                  '-c',
                  '100.64.0.1', '-t', '10', '-p', '{}'.format(ApplicationStartPort + learnerNum), '1000',
                  'http://100.64.0.1:{}'.format(LearnerStartPort + learnerNum)])
                , ('http://localhost:8079', ['iperf3', '-s', '-p', '{}'.format(ApplicationStartPort + learnerNum)])
            ]

            experiments.experiments_common.runExperiment(NetworkNodes, singleUseLearnerConfig, singleUseAppCommand, ExperimentLengthSeconds,
                                                     PostTestTimeBufferSecods, PostTestTimeBufferSecods, DirOffset,
                                                     True)

    # Test together
    traceLabel = 'tst-together'
    for index in range(0, TestingCount):

        # setup learners
        learners = []

        # setup applications
        applications = []

        for learnerNum in range(0, NumberOfLearners):

            singleUseLearnerConfig = [(LearnerName, '{}'.format(LearnerStartPort + learnerNum), '', '0', LearnerLabel.format(learnerNum, learnerLabel), traceLabel, '')]

            learners.extend(singleUseLearnerConfig.copy())

            singleUseAppCommand = [
                ('http://100.64.0.2:8079',
                 ['python3', DirOffset + 'applications/Iperf/experiment_02_congestion_control_micro/iperf_stub.py',
                  '-c',
                  '100.64.0.1', '-t', '10', '-p', '{}'.format(ApplicationStartPort + learnerNum), '1000',
                  'http://100.64.0.1:{}'.format(LearnerStartPort + learnerNum)])
                , ('http://localhost:8079', ['iperf3', '-s', '-p', '{}'.format(ApplicationStartPort + learnerNum)])
            ]

            applications.extend(singleUseAppCommand.copy())

        experiments.experiments_common.runExperiment(NetworkNodes, learners, applications, ExperimentLengthSeconds, PostTestTimeBufferSecods, PostTestTimeBufferSecods, DirOffset, True)

    # Test seperately
    traceLabel = 'tst-seperate'
    for index in range(0, TestingCount):

        for learnerNum in range(0, NumberOfLearners):
            singleUseLearnerConfig = [(LearnerName, '{}'.format(LearnerStartPort + learnerNum), '', '0',
                                       LearnerLabel.format(learnerNum, learnerLabel), traceLabel, '')]

            singleUseAppCommand = [
                ('http://100.64.0.2:8079',
                 ['python3', DirOffset + 'applications/Iperf/experiment_02_congestion_control_micro/iperf_stub.py',
                  '-c',
                  '100.64.0.1', '-t', '10', '-p', '{}'.format(ApplicationStartPort + learnerNum), '1000',
                  'http://100.64.0.1:{}'.format(LearnerStartPort + learnerNum)])
                , ('http://localhost:8079', ['iperf3', '-s', '-p', '{}'.format(ApplicationStartPort + learnerNum)])
            ]

            experiments.experiments_common.runExperiment(NetworkNodes, singleUseLearnerConfig, singleUseAppCommand, ExperimentLengthSeconds,
                                                     PostTestTimeBufferSecods, PostTestTimeBufferSecods, DirOffset,
                                                     True)

    # Verify together
    traceLabel = 'vrf-together'
    for index in range(0, ValidationCount):

        for validationPattern in ValidationPatterns:

            # setup learners
            learners = []

            # setup applications
            applications = []

            for learnerNum in range(0, NumberOfLearners):
                singleUseLearnerConfig = [(LearnerName, '{}'.format(LearnerStartPort + learnerNum), '', '2',
                                           'validator-{}'.format(index), traceLabel, validationPattern)]

                learners.extend(singleUseLearnerConfig.copy())

                singleUseAppCommand = [
                    ('http://100.64.0.2:8079',
                     ['python3', DirOffset + 'applications/Iperf/experiment_02_congestion_control_micro/iperf_stub.py',
                      '-c',
                      '100.64.0.1', '-t', '10', '-p', '{}'.format(ApplicationStartPort + learnerNum), '1000',
                      'http://100.64.0.1:{}'.format(LearnerStartPort + learnerNum)])
                    , ('http://localhost:8079', ['iperf3', '-s', '-p', '{}'.format(ApplicationStartPort + learnerNum)])
                ]

                applications.extend(singleUseAppCommand.copy())

            experiments.experiments_common.runExperiment(NetworkNodes, learners, applications, ExperimentLengthSeconds,
                                                         PostTestTimeBufferSecods, PostTestTimeBufferSecods, DirOffset,
                                                         True)

    # Verify seperatelys
    traceLabel = 'vrf-seperate'
    for index in range(0, ValidationCount):

        for validationPattern in ValidationPatterns:

            for learnerNum in range(0, NumberOfLearners):
                singleUseLearnerConfig = [(LearnerName, '{}'.format(LearnerStartPort + learnerNum), '', '2',
                                           'validator-{}'.format(index), traceLabel, validationPattern)]

                singleUseAppCommand = [
                    ('http://100.64.0.2:8079',
                     ['python3', DirOffset + 'applications/Iperf/experiment_02_congestion_control_micro/iperf_stub.py',
                      '-c',
                      '100.64.0.1', '-t', '10', '-p', '{}'.format(ApplicationStartPort + learnerNum), '1000',
                      'http://100.64.0.1:{}'.format(LearnerStartPort + learnerNum)])
                    , ('http://localhost:8079', ['iperf3', '-s', '-p', '{}'.format(ApplicationStartPort + learnerNum)])
                ]

                experiments.experiments_common.runExperiment(NetworkNodes, singleUseLearnerConfig, singleUseAppCommand, ExperimentLengthSeconds,
                                                         PostTestTimeBufferSecods, PostTestTimeBufferSecods, DirOffset,
                                                         True)

except KeyboardInterrupt:
    print('')
except Exception as ex:
    print(str(ex))
