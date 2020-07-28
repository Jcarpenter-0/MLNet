# Simple Ping experiment to show abilities of learner and platform

# Setup the dir
DirOffset = '../../'

import os
import sys
sys.path.insert(0, os.getcwd())
sys.path.insert(0, DirOffset)
import experiments.experiments_common

# Define Learners as tuple (<name of learner>, <port>, <mode>, <model name>, (optional) <validation pattern file path>)
Learners = [('example_ping_manager',  '8080', '', '2', 'exp-02-ping-learner', '', './pattern-0.csv')
            ]

# Define Network as tuple for each node (<[script commands to setup a node and the server code]>)
NetworkNodes = [['mm-delay', '20', 'python3', DirOffset + 'applications/operation-server.py', '8081']
                ]

# Define Applications as tuple (<host address>, <[args to the application]>)
Applications = [('http://100.64.0.2:8081', ['python3', DirOffset + 'applications/Ping/Ping.py', '100.64.0.1', '-c', '10', '-s', '56', '-t', '255', '1000', 'http://100.64.0.1:8080'])
                ]

experiments.experiments_common.runExperiment(NetworkNodes, Learners, Applications, 1800, 10, 10, DirOffset)
