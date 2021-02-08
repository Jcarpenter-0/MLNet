import numpy as np
import glob
import random
import math

DirOffset = ''
if __name__ == '__main__':
    # Setup the dir
    DirOffset = '../../'

    import os
    import sys
    sys.path.insert(0, os.getcwd())
    sys.path.insert(0, DirOffset)

import networks.mahimahi
import learners
import apps.Iperf
import exps

# Experiment Parameters
TraceDir = './mahimahi-traces/'
DelayRanges = range(10, 30, 10)
VerificationPatternFiles = ['./bbr-pattern.csv', './cubic-pattern.csv', './reno-pattern.csv', './vegas-pattern.csv']
ExperimentRunTime = 30

# Get the traces
Traces = glob.glob(TraceDir + '*')

# Calculate the test duration
Testcount = (len(Traces) * len(DelayRanges)) + (len(Traces) * len(DelayRanges) * len(VerificationPatternFiles))
TestTime = ExperimentRunTime * Testcount

print('Tests planned {} - Time ~{} hours'.format(Testcount, TestTime/60/60))
input("Press Enter to continue... or ctrl-c to stop")

for trace in Traces:

    traceName = trace.split('.')[-2].split('/')[-1]

    # for each delay value
    for delay in DelayRanges:

        envDescriptor = 'env-delay-{}-{}.mm'.format(delay, traceName)

        # Setup the environment
        mmShells = list()

        mmShells.append(networks.mahimahi.MahiMahiDelayShell(delay))
        mmShells.append(networks.mahimahi.MahiMahiLinkShell(upLinkTraceFilePath=trace
                                                            , downLinkTraceFilePath=trace
                                                            , uplinkQueue='droptail', uplinkQueueArgs='packets=400'
                                                            , downlinkQueue='droptail', downlinkQueueArgs='packets=400',
                                                            uplinkLogFilePath='./data/{}'.format(envDescriptor)))

        node, baseAddress = networks.mahimahi.SetupMahiMahiNode(mmShells, dirOffset=DirOffset)

        serverNode = networks.SetupLocalHost(ipAddress=baseAddress)

        network = networks.NetworkModule(nodes=[serverNode, node])

        # Run the learner
        learner = learners.Learner(
            '{}./learners/congestion_control_manager/congestion_control_manager.py'.format(DirOffset))

        serverNode.AddApplication(learner.ToArgs())

        serverNode.AddApplication(['iperf', '-s'])

        node.AddApplication(apps.Iperf.PrepIperfCall(serverNode.IpAddress, serverNode.IpAddress, learner.LearnerPort, 1, 10))

        exps.runExperimentUsingFramework(network, ExperimentRunTime)

        network.Shutdown()

        # Run the benchmarks
        print('Running Validations')
        for vefPattern in VerificationPatternFiles:

            ccPattern = vefPattern.split('-')[0].split('/')[-1]

            mmShells = list()

            mmShells.append(networks.mahimahi.MahiMahiDelayShell(delay))
            mmShells.append(networks.mahimahi.MahiMahiLinkShell(upLinkTraceFilePath=trace
                                                                , downLinkTraceFilePath=trace
                                                                , uplinkQueue='droptail', uplinkQueueArgs='packets=400'
                                                                , downlinkQueue='droptail',
                                                                downlinkQueueArgs='packets=400',
                                                                uplinkLogFilePath='./data/{}-verf-{}'.format(ccPattern,envDescriptor)))

            node, baseAddress = networks.mahimahi.SetupMahiMahiNode(mmShells, dirOffset=DirOffset)

            serverNode = networks.SetupLocalHost(ipAddress=baseAddress)

            network = networks.NetworkModule(nodes=[serverNode, node])

            learner = learners.Learner(
                '{}./learners/congestion_control_manager/congestion_control_manager.py'.format(DirOffset)
                , training=2
                , traceFilePostFix='pattern-{}'.format(ccPattern)
                , miscArgs=[vefPattern])


            serverNode.AddApplication(learner.ToArgs())

            serverNode.AddApplication(['iperf', '-s'])

            node.AddApplication(apps.Iperf.PrepIperfCall(serverNode.IpAddress, serverNode.IpAddress, learner.LearnerPort, 1, 10, ccPattern))

            exps.runExperimentUsingFramework(network, ExperimentRunTime)

            network.Shutdown()
