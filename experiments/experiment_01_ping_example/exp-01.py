# Simple Ping experiment to show abilities of learner and platform

# Setup the dir
DirOffset = '../../'

import os
import sys
sys.path.insert(0, os.getcwd())
sys.path.insert(0, DirOffset)
import experiments.common
import networks.mahimahi
import networks.common

# Define Learners
pingManager = experiments.common.Learner('../../learners/example_ping_manager/ping_manager.py')

pingManagerVerification = experiments.common.Learner('../../learners/example_ping_manager/ping_manager.py')

# Define network nodes
pingNode = networks.mahimahi.SetupMahiMahiNode([networks.mahimahi.MahiMahiDelayShell(delayMS=10)], dirOffset=DirOffset)

pingNode.AddApplication(['python3', '{}applications/Ping/Ping.py'.format(DirOffset), '100.64.0.1', '-c', '10', '-s', '56', '-t', '255',
                         '1000', 'http://100.64.0.1:{}'.format(pingManager.LearnerPort)])

# run experiment
experiments.common.runExperimentUsingFramework([pingNode], [pingManager], 30)
