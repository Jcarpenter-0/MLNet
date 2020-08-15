# Simple CC experiment, involving two nodes
import numpy as np

# Setup the dir
DirOffset = '../../'

import os
import sys
sys.path.insert(0, os.getcwd())
sys.path.insert(0, DirOffset)
import experiments.experiments_common
import learners.learner_common

ExperimentLengthSeconds = 1800

# Number of iperf runs to attempt
IperfRuns = 1000

# How long the iperf runs should attempt to go for
IperfRunLengthSeconds = 10

# Post-test cooldown
PostTestTimeBufferSecods = 10

# For other time estimations
ArbitraryTimeAddSeconds = 7

# Train, Validate, then Test
LearnerModes = ['1', '0']
# Number of times to run validation
ValidationCount = 1
ValidationPatterns = [
    './cubic-pattern.csv',
    './bbr-pattern.csv',
    './vegas-pattern.csv',
    './reno-pattern.csv'
]

Topologies = []

# Generate Topology args
for delay in range(10, 20, 10):
    delayCommand = ['mm-delay', '{}'.format(delay)]
    Topologies.append(delayCommand)

for linkDirection in ['uplink', 'downlink']:

    for lossRate in np.arange(0.1, 0.2, 0.1):
        lossCommand = ['mm-loss', linkDirection, '{}'.format(lossRate)]
        Topologies.append(lossCommand)

VariationCount = (len(LearnerModes) * len(Topologies)) + (len(ValidationPatterns) * ValidationCount)
print('Tests planned {} - Time ~{} hours'.format(VariationCount, ((ExperimentLengthSeconds + (2 * PostTestTimeBufferSecods) + ArbitraryTimeAddSeconds) * VariationCount)/60/60))
input("Press Enter to continue... or ctrl-c to stop")

CurrentTestID = 0

try:

    for topo in Topologies:

        print('Test {}/{}'.format(CurrentTestID, VariationCount))
        learnerName = 'exp-02-cc-learner-{}'.format(CurrentTestID)
        logPrefix = 'env'

        NetworkArg = topo.copy()

        NetworkArg.extend(['python3', DirOffset + 'applications/operation_server.py', '8081'])

        for topoPara in topo:
            logPrefix += '-{}'.format(topoPara)

        for learnerMode in LearnerModes:

            # Define Learners as tuple (<name of learner>, <port>, <mode>, <model name>, (optional) <validation pattern file path> (optional) <tracefile prefix>)
            Learners = [('congestion_control_manager_micro', '8080', '', learnerMode, learnerName, logPrefix, '')
                        ]

            # Define Network as tuple for each node (<[script commands to setup a node and the server code]>)
            NetworkNodes = [NetworkArg,
                            ['python3', DirOffset + 'applications/operation_server.py', '8081']
                ]

            # Define Applications as tuple (<host address>, <[args to the application]>)
            Applications = [('http://100.64.0.2:8081', [
                'python3'
                , DirOffset + 'applications/Iperf/experiment_02_congestion_control_micro/iperf_stub.py'
                ,'-c', '100.64.0.1', '-t', '{}'.format(IperfRunLengthSeconds), '{}'.format(IperfRuns), 'http://100.64.0.1:8080'])
                , ('http://localhost:8081', ['iperf3', '-s'])
                            ]

            experiments.experiments_common.runExperiment(NetworkNodes, Learners, Applications, ExperimentLengthSeconds, PostTestTimeBufferSecods, PostTestTimeBufferSecods, DirOffset, True)
            CurrentTestID += 1

        # Do validation runs
        for validationPattern in ValidationPatterns:

            for validationIteration in range(0, ValidationCount):
                # Define Learners as tuple (<name of learner>, <port>, <mode>, <model name>, (optional) <validation pattern file path> (optional) <tracefile prefix>)
                Learners = [('congestion_control_manager_micro', '8080', '', '2', learnerName, logPrefix, validationPattern)
                                ]

                # Define Network as tuple for each node (<[script commands to setup a node and the server code]>)
                NetworkNodes = [NetworkArg,
                                ['python3', DirOffset + 'applications/operation_server.py', '8081']
                                ]

                # Define Applications as tuple (<host address>, <[args to the application]>)
                Applications = [('http://100.64.0.2:8081', [
                    'python3'
                    , DirOffset + 'applications/Iperf/experiment_02_congestion_control_micro/iperf_stub.py'
                    , '-c', '100.64.0.1', '-t', '{}'.format(IperfRunLengthSeconds), '{}'.format(IperfRuns),
                    'http://100.64.0.1:8080'])
                    , ('http://localhost:8081', ['iperf3', '-s'])
                                ]

                experiments.experiments_common.runExperiment(NetworkNodes, Learners, Applications, ExperimentLengthSeconds, PostTestTimeBufferSecods, PostTestTimeBufferSecods,
                                                                 DirOffset, True)
                CurrentTestID += 1

except KeyboardInterrupt:
    print('')
except Exception as ex:
    print(str(ex))