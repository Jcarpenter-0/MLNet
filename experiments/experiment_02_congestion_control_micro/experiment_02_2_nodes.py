# Simple CC experiment, involving two nodes
import numpy as np

# Setup the dir
DirOffset = '../../'

import os
import sys
sys.path.insert(0, os.getcwd())
sys.path.insert(0, DirOffset)
import experiments.experiments_common

ExperimentLengthSeconds = 1800


# Train, Validate, then Test
LearnerModes = ['1', '0']
Topologies = [['mm-delay', range(10, 40, 10)], ['mm-loss uplink', np.arange(0, .1, .01)], ['mm-loss downlink', np.arange(0, .1, .01)]]

# Number of times to run validation
ValidationCount = 1
ValidationPatterns = ['./pattern-0.txt', './pattern-1.txt', './pattern-2.txt', './pattern-3.txt']

VariationCount = (len(LearnerModes) * len(Topologies[0][1]) * len(Topologies[1][1])) + (len(ValidationPatterns) * ValidationCount)
print('Tests {}'.format(VariationCount))


CurrentTestID = 0

for topo in Topologies:

    topoCommand = topo[0]

    for topoPara in topo[1]:

        print('Test {}/{}'.format(CurrentTestID, VariationCount))
        learnerName = 'exp-02-cc-learner-{}'.format(CurrentTestID)
        logPrefix = 'env-{}-{}'.format(topoCommand, topoPara)

        for learnerMode in LearnerModes:

            # Define Learners as tuple (<name of learner>, <port>, <mode>, <model name>, (optional) <validation pattern file path> (optional) <tracefile prefix>)
            Learners = [('congestion_control_manager_micro', '8080', '', learnerMode, learnerName, logPrefix, '')
                        ]

            # Define Network as tuple for each node (<[script commands to setup a node and the server code]>)
            NetworkNodes = [['{}'.format(topoCommand), '{}'.format(topoPara), 'python3', DirOffset + 'applications/operation-server.py', '8081']
                , ['python3', DirOffset + 'applications/operation-server.py', '8081']
                            ]

            # Define Applications as tuple (<host address>, <[args to the application]>)
            Applications = [('http://100.64.0.2:8081', ['python3',
                                                        DirOffset + 'applications/Iperf/experiment_02_congestion_control_micro/iperf_stub.py',
                                                        '1000', 'http://100.64.0.1:8080', '-c|100.64.0.1'])
                , ('http://localhost:8081', ['iperf3', '-s'])
                            ]

            experiments.experiments_common.runExperiment(NetworkNodes, Learners, Applications, ExperimentLengthSeconds, 10, 10, DirOffset)

        # Do validation runs
        for validationPattern in ValidationPatterns:

            for validationIteration in range(0, ValidationCount):
                # Define Learners as tuple (<name of learner>, <port>, <mode>, <model name>, (optional) <validation pattern file path> (optional) <tracefile prefix>)
                Learners = [('congestion_control_manager_micro', '8080', '2', learnerName, validationPattern, logPrefix)
                            ]

                # Define Network as tuple for each node (<[script commands to setup a node and the server code]>)
                NetworkNodes = [['{}'.format(topoCommand), '{}'.format(topoPara), 'python3',
                                 DirOffset + 'applications/operation-server.py', '8081']
                    , ['python3', DirOffset + 'applications/operation-server.py', '8081']
                                ]

                # Define Applications as tuple (<host address>, <[args to the application]>)
                Applications = [('http://100.64.0.2:8081', ['python3',
                                                            DirOffset + 'applications/Iperf/experiment_02_congestion_control_micro/iperf_stub.py',
                                                            '1000', 'http://100.64.0.1:8080', '-c|100.64.0.1'])
                    , ('http://localhost:8081', ['iperf3', '-s'])
                                ]

                experiments.experiments_common.runExperiment(NetworkNodes, Learners, Applications, ExperimentLengthSeconds, 10, 10,
                                                             DirOffset)

        CurrentTestID += 1
