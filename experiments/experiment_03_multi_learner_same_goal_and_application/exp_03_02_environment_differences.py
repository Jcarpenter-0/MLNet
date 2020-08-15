import numpy as np

# Does a learner handle environments drastically different from training well?

# Take a learner, train in environment A, then test in a different environment A~ such that conditions are noticeably different

# Setup the dir
DirOffset = '../../'

import os
import sys
sys.path.insert(0, os.getcwd())
sys.path.insert(0, DirOffset)
import experiments.experiments_common

# for each topology, train on it, then test on it and the others

# How many times to train/test on each topology
TrainingCount = 2
TestingCount = 2

Topologies = []

# Fill in topologies
# Generate Topology args
for delay in range(0, 50, 50):
    delayCommand = ['mm-delay', '{}'.format(delay)]
    Topologies.append(delayCommand)

for linkDirection in ['uplink', 'downlink']:

    for lossRate in np.arange(0.0, 0.1, 0.1):
        lossCommand = ['mm-loss', linkDirection, '{}'.format(lossRate)]
        Topologies.append(lossCommand)

ValidationPatterns = [
    './cubic-pattern.csv',
    './bbr-pattern.csv',
    './vegas-pattern.csv',
    './reno-pattern.csv'
]

ExperimentLengthSeconds = 1800

# Post-test cooldown
PostTestTimeBufferSecods = 10

# For other time estimations
ArbitraryTimeAddSeconds = 7


# =================================================================================================

TestCount = (len(Topologies)) * ((TrainingCount) + (len(ValidationPatterns) * TestingCount) + (TestingCount * len(Topologies)))
TestTimeEstimate = TestCount * (ExperimentLengthSeconds + PostTestTimeBufferSecods + ArbitraryTimeAddSeconds)
print('Tests planned {} - Time ~{} hours'.format(TestCount, (TestTimeEstimate / 60 / 60)))
input("Press Enter to continue... or ctrl-c to stop")


LocalSideNetworkingArg = ['python3', DirOffset + 'applications/operation_server.py', '8081']

# Number of iperf runs to attempt
IperfRuns = 1000

# How long the iperf runs should attempt to go for
IperfRunLengthSeconds = 10

Applications = [
    ('http://100.64.0.2:8081',['python3', DirOffset + 'applications/Iperf/experiment_02_congestion_control_micro/iperf_stub.py', '-c', '100.64.0.1', '-t', '{}'.format(IperfRunLengthSeconds), '{}'.format(IperfRuns), 'http://100.64.0.1:8080'])
    , ('http://localhost:8081', ['iperf3', '-s'])
            ]

LearnerName = 'congestion_control_manager_micro'
LearnerPort = '8080'
LearnerAddr = ''
LearnerLabel = 'exp-03-02-{}-{}'
LearnerLogPrefix = '{}'

for testID, trainingTopo in enumerate(Topologies):

    print('On topology {}/{}'.format(testID, len(Topologies)))

    trainingenvLabel = 'trn-env'

    for topoPara in trainingTopo:
        trainingenvLabel += '-{}'.format(topoPara)

    trainingNetworkingArg = trainingTopo.copy()

    trainingNetworkingArg.extend(LocalSideNetworkingArg)

    trainingNetworkNodes = [trainingNetworkingArg,
                    LocalSideNetworkingArg
                    ]

    # Train on one environment
    for index in range(0, TrainingCount):

        trainingLearners = [(LearnerName, LearnerPort, LearnerAddr, '1', LearnerLabel.format(testID, trainingenvLabel), trainingenvLabel, '')]

        experiments.experiments_common.runExperiment(trainingNetworkNodes, trainingLearners, Applications, ExperimentLengthSeconds, PostTestTimeBufferSecods, PostTestTimeBufferSecods, DirOffset, True)


    # Test on all the other topologies
    for index in range(0, TestingCount):
        for testingTopo in Topologies:

            # Make testing env label
            testingEnvLabel = 'tst-env'

            for topoPara in testingTopo:
                testingEnvLabel += '-{}'.format(topoPara)

            # Setup Network Args
            testingNetworkArg = testingTopo.copy()

            testingNetworkArg.extend(LocalSideNetworkingArg)

            testingNetworkNodes = [testingNetworkArg,
                            LocalSideNetworkingArg
                            ]

            testingLearners = [
                (LearnerName, LearnerPort, LearnerAddr, '0', LearnerLabel.format(testID, trainingenvLabel), testingEnvLabel, '')]

            # Test the model
            experiments.experiments_common.runExperiment(testingNetworkNodes, testingLearners, Applications,
                                                         ExperimentLengthSeconds, PostTestTimeBufferSecods,
                                                         PostTestTimeBufferSecods, DirOffset, True)

            # Verify the Environment
            for validationPattern in ValidationPatterns:

                verifiers = [
                    (LearnerName, LearnerPort, LearnerAddr, '2', LearnerLabel.format(testID, validationPattern), testingEnvLabel, validationPattern)]

                experiments.experiments_common.runExperiment(testingNetworkNodes, verifiers, Applications,
                                                             ExperimentLengthSeconds, PostTestTimeBufferSecods,
                                                             PostTestTimeBufferSecods, DirOffset, True)

