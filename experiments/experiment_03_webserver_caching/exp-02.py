# Setup the dir
DirOffset = '../../'

import os
import sys
sys.path.insert(0, os.getcwd())
sys.path.insert(0, DirOffset)
import experiments.experiments_common

# Define Learners as tuple (<name of learner>, <port>, <mode>, <model name>, (optional) <validation pattern file path>)
Learners = [('http_server_caching', '8080', '1', 'exp-03-http-cache-learner', './pattern-0.txt')
            ]

# Define Network as tuple for each node (<[script commands to setup a node and the server code]>)
NetworkNodes = [['mm-delay', '40', 'python3', DirOffset + 'applications/operation-server.py', '8081']
                ,['python3', DirOffset + 'applications/operation-server.py', '8081']
                ]

# Define Applications as tuple (<host address>, <[args to the application]>)
Applications = [('http://100.64.0.2:8081', ['python3', DirOffset + 'applications/PythonHttpWebServer/run-server.py', '8082', '', 'http://100.64.0.1:8080'])
                ,('http://localhost:8081', ['python3', DirOffset + 'applications/Chromium/run-stub.py', '1000', 'http://100.64.0.2:8082', ''])
                ]

experiments.experiments_common.runExperiment(NetworkNodes, Learners, Applications, 1800, 10, 10, DirOffset)
