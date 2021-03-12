import numpy as np
import glob
import random
import math

# Setup the dir
DirOffset = '../../'

import os
import sys
sys.path.insert(0, os.getcwd())
sys.path.insert(0, DirOffset)
import networks.mahimahi
import networks.common
import exps.common

# Experiment Parameters
TestRepetitions = 10
ExperimentRunTime = 1900
IperfRunCount = 1000
IperfRunLength = 10

# Environment Ranges
MMDelayRange = range(0, 1100, 100)
Topologies = []

for delay in MMDelayRange:
    Topologies.append(networks.mahimahi.MahiMahiDelayShell(delay))

# Do the meta calculations
NumberOfTests = len(Topologies) * (len(Topologies) * TestRepetitions)
TotalTimeInSeconds = NumberOfTests * ExperimentRunTime

print('Tests planned {} - Time ~{} hours'.format(NumberOfTests, TotalTimeInSeconds/60/60))
input("Press Enter to continue... or ctrl-c to stop")

# For each Environment, train a model for it, evaluate it
for topo in Topologies:

    # Train
    # Setup the learners
    ccLearner = exps.common.Learner(
        '{}learners/congestion_control_manager/congestion_control_manager.py'.format(DirOffset)
        , traceFilePostFix=topo.GetParaString() + '_trn'
        , learnerDir='./tmp/' + topo.GetParaString() + '/')

    # Define network nodes
    iperfClientNode = networks.common.SetupLocalHost(dirOffset=DirOffset)

    iperfServerNode = networks.mahimahi.SetupMahiMahiNode([topo], dirOffset=DirOffset)

    iperfClientNode.AddApplication(
        ['python3', '{}applications/Iperf/0X_cc_manager/iperf_stub.py'.format(DirOffset)
            , '-c', '{}'.format(iperfServerNode.IpAddress), '-t', '{}'.format(IperfRunLength),
         '{}'.format(IperfRunCount), 'http://localhost:{}'.format(ccLearner.LearnerPort)])

    iperfServerNode.AddApplication(['iperf3', '-s'])

    # run experiment
    exps.common.runExperimentUsingFramework([iperfServerNode, iperfClientNode], [ccLearner], ExperimentRunTime,
                                            learnerServerCooldown=30)

    # Test on all the other topologies
    for testTopo in Topologies:

        for testRep in range(0, TestRepetitions):
            # Setup the learners
            testingLearner = exps.common.Learner(
                '{}learners/congestion_control_manager/congestion_control_manager.py'.format(DirOffset)
                , training=0
                , traceFilePostFix=testTopo.GetParaString() + '_tst_{}'.format(testRep)
                , learnerDir=ccLearner.LearnerDir)

            # Define network nodes
            iperfClientNode = networks.common.SetupLocalHost(dirOffset=DirOffset)

            iperfServerNode = networks.mahimahi.SetupMahiMahiNode([testTopo], dirOffset=DirOffset)

            iperfServerNode.AddApplication(['iperf3', '-s'])

            iperfClientNode.AddApplication(
                ['python3', '{}applications/Iperf/0X_cc_manager/iperf_stub.py'.format(DirOffset)
                    , '-c', '100.64.0.1', '-t', '{}'.format(IperfRunLength),
                 '{}'.format(IperfRunCount), 'http://localhost:{}'.format(testingLearner.LearnerPort)])

            # run experiment
            exps.common.runExperimentUsingFramework([iperfServerNode, iperfClientNode], [testingLearner],
                                                    ExperimentRunTime, learnerServerCooldown=30)

print('Experiment Done')
