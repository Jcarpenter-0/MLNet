# Setup the dir
DirOffset = '../../'

import os
import sys
sys.path.insert(0, os.getcwd())
sys.path.insert(0, DirOffset)
import experiments.experiments_common

# Define Learners as tuple (<name of learner>, <port>, <training flag>)
Learners = [('example', '8080', '1')
            ]

# Define Network as tuple for each node (<[script commands to setup a node and the server code]>)
NetworkNodes = [['python3', DirOffset + 'applications/operation-server.py', '8081']
                ]

# Define Applications as tuple (<host address>, <[args to the application]>)
Applications = [('http://localhost:8081', ['python3', DirOffset + 'applications/tracereader/tracereader.py', 'http://localhost:8080', DirOffset + 'applications/tracereader/traintrace.csv'])
                ]
experiments.experiments_common.runExperiment(NetworkNodes, Learners, Applications, 25, 10, 10, DirOffset)
