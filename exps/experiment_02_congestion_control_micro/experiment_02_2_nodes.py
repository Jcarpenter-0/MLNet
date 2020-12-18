# Simple CC experiment, involving two nodes
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

# Experiment Parameters
TraceDir = './mahimahi-traces/'
TrainPercentage = 0.80
TestPercentage = 1 - TrainPercentage
TestRepetitions = 2
VerificationPatternFiles = ['./bbr-pattern.csv', './cubic-pattern.csv', './reno-pattern.csv', './vegas-pattern.csv']
ExperimentRunTime = 1900
IperfRunCount = 1000
IperfRunLength = 10

# Get the traces
Traces = glob.glob(TraceDir + '*')
TrainingTracesCount = math.ceil(len(Traces) * TrainPercentage)
TestingTracesCount = math.floor(len(Traces) * TestPercentage)

# Build the topologies (environments)
Topologies = []

for traceFile in Traces:
    Topologies.append(networks.mahimahi.MahiMahiLinkShell(traceFile, traceFile))

# Divide into training and testing, select randomly from the whole set
TestingTopologies = []
TrainingTopologies = []

topoCopy = Topologies.copy()

for trainingNum in range(0, TrainingTracesCount):
    # Select a trace
    traceIndex = random.randint(0, len(topoCopy)-1)
    trace = topoCopy.pop(traceIndex)
    TrainingTopologies.append(trace)

# Remaining traces are for testing
TestingTopologies.extend(topoCopy)

# Do the meta calculations
NumberOfTests = len(TrainingTopologies) + (len(TestingTopologies) * TestRepetitions) + (len(TestingTopologies) * TestRepetitions * len(VerificationPatternFiles))
TotalTimeInSeconds = NumberOfTests * ExperimentRunTime

print('Tests planned {} - Time ~{} hours'.format(NumberOfTests, TotalTimeInSeconds/60/60))
input("Press Enter to continue... or ctrl-c to stop")

# Train
for trnEnv in TrainingTopologies:

    # Setup the learners
    ccLearner = exps.Learner(
        '{}learners/congestion_control_manager/congestion_control_manager.py'.format(DirOffset)
        , traceFilePostFix=trnEnv.GetParaString() + '_trn')

    # Define network nodes
    iperfClientNode = networks.common.SetupLocalHost(dirOffset=DirOffset)

    iperfServerNode = networks.mahimahi.SetupMahiMahiNode([trnEnv], dirOffset=DirOffset)

    iperfClientNode.AddApplication(
        ['python3', '{}applications/Iperf/experiment_02_congestion_control_micro/iperf_stub.py'.format(DirOffset)
            ,'-c', '{}'.format(iperfServerNode.IpAddress), '-t', '{}'.format(IperfRunLength),
         '{}'.format(IperfRunCount), 'http://localhost:{}'.format(ccLearner.LearnerPort)])

    iperfServerNode.AddApplication(['iperf3', '-s'])

    # run experiment
    exps.runExperimentUsingFramework([iperfServerNode, iperfClientNode], [ccLearner], ExperimentRunTime, learnerServerCooldown=30)

# Test
for tstEnv in TestingTopologies:

    for testRep in range(0, TestRepetitions):
        # Setup the learners
        ccLearner = exps.Learner(
            '{}learners/congestion_control_manager/congestion_control_manager.py'.format(DirOffset)
            , training=0
            , traceFilePostFix=tstEnv.GetParaString() + '_tst_{}'.format(testRep))

        # Define network nodes
        iperfClientNode = networks.common.SetupLocalHost(dirOffset=DirOffset)

        iperfServerNode = networks.mahimahi.SetupMahiMahiNode([tstEnv], dirOffset=DirOffset)

        iperfClientNode.AddApplication(
            ['python3', '{}applications/Iperf/experiment_02_congestion_control_micro/iperf_stub.py'.format(DirOffset)
                , '-c', '100.64.0.1', '-t', '{}'.format(IperfRunLength),
             '{}'.format(IperfRunCount), 'http://localhost:{}'.format(ccLearner.LearnerPort)])

        iperfServerNode.AddApplication(['iperf3', '-s'])

        # run experiment
        exps.runExperimentUsingFramework([iperfServerNode, iperfClientNode], [ccLearner],
                                                ExperimentRunTime, learnerServerCooldown=30)

# Verify
for tstEnv in TestingTopologies:

    for testRep in range(0, TestRepetitions):

        for verPattern in VerificationPatternFiles:
            # Setup the learners
            ccLearner = exps.Learner(
                '{}learners/congestion_control_manager/congestion_control_manager.py'.format(DirOffset)
                , training=2
                , traceFilePostFix=tstEnv.GetParaString() + '_{}_{}'.format(testRep, verPattern.replace('.','').replace('/',''))
                , miscArgs=[verPattern])

            # Define network nodes
            iperfClientNode = networks.common.SetupLocalHost(dirOffset=DirOffset)

            iperfServerNode = networks.mahimahi.SetupMahiMahiNode([tstEnv], dirOffset=DirOffset)

            iperfClientNode.AddApplication(
                ['python3',
                 '{}applications/Iperf/experiment_02_congestion_control_micro/iperf_stub.py'.format(DirOffset)
                    , '-c', '100.64.0.1', '-t', '{}'.format(IperfRunLength),
                 '{}'.format(IperfRunCount), 'http://localhost:{}'.format(ccLearner.LearnerPort)])

            iperfServerNode.AddApplication(['iperf3', '-s'])

            # run experiment
            exps.runExperimentUsingFramework([iperfServerNode, iperfClientNode], [ccLearner],
                                                    ExperimentRunTime, learnerServerCooldown=30)

print('Experiment Done')
