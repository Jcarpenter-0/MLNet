# Simple Ping experiment to show abilities of learner and platform

# Setup the dir
DirOffset = '../../'

import os
import sys
sys.path.insert(0, os.getcwd())
sys.path.insert(0, DirOffset)
import experiments.experiments_common
import learners.learner_server
import applications.operation_server

# Define Learners as tuple (<name of learner>, <port>, <mode>, <model name>, (optional) <validation pattern file path>)
Learners = [learners.learner_server.LearnerNode('example_ping_manager', dirOffset=DirOffset).ToArgs()]

netArgs = ['mm-delay', '20']

netArgs.extend(applications.operation_server.PrepareOperationServerArgs(dirOffset=DirOffset))

# Define Applications as tuple (<host address>, <[args to the application]>)
Applications = [('http://100.64.0.2:8081', ['python3', DirOffset + 'applications/Ping/Ping.py', '100.64.0.1', '-c', '10', '-s', '56', '-t', '255', '1000', 'http://100.64.0.1:8080'])]

experiments.experiments_common.runExperiment([netArgs], Learners, Applications, 1800, 10, 10, DirOffset)
