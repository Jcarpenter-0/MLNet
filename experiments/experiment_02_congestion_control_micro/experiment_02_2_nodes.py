# Simple CC experiment, involving two nodes

# Setup the dir
DirOffset = '../../'

import os
import sys
sys.path.insert(0, os.getcwd())
sys.path.insert(0, DirOffset)
import experiments.experiments_common

# Define Learners as tuple (<name of learner>, <port>, <mode>, <model name>, (optional) <validation pattern file path>)
Learners = [('congestion_control_manager_micro', '8080', '1', 'exp-02-cc-learner', './SimpleValidationPattern.txt')
            ]

# Define Network as tuple for each node (<[script commands to setup a node and the server code]>)
NetworkNodes = [['mm-delay', '40', 'python3', DirOffset + 'applications/operation-server.py', '8081']
                ,['python3', DirOffset + 'applications/operation-server.py', '8081']
                ]

# Define Applications as tuple (<host address>, <[args to the application]>)
Applications = [('http://100.64.0.2:8081', ['python3', DirOffset + 'applications/Iperf/experiment_02_congestion_control_micro/iperf_stub.py', '1000', 'http://100.64.0.1:8080', '-c|100.64.0.1'])
                ,('http://localhost:8081', ['iperf3', '-s'])
                ]

experiments.experiments_common.runExperiment(NetworkNodes, Learners, Applications, 1800, 10, 10, DirOffset)
