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
import apps.Iperf3
import exps

# Testing Macro Settings
VerificationPatternFiles = ['./vegas-pattern.csv']
                            #'./bbr-pattern.csv', './cubic-pattern.csv', './reno-pattern.csv']

# Build the environment
mmShells = list()

mmShells.append(networks.mahimahi.MahiMahiDelayShell(25))
mmShells.append(networks.mahimahi.MahiMahiLinkShell(upLinkTraceFilePath='./const48.mahi', downLinkTraceFilePath='./const48.mahi'
                                                    , uplinkQueue='droptail', uplinkQueueArgs='packets=400'
                                                    , downlinkQueue='droptail', downlinkQueueArgs='packets=400', uplinkLogFilePath='./data/up-log'))

node, baseAddress = networks.mahimahi.SetupMahiMahiNode(mmShells, dirOffset=DirOffset)

serverNode = networks.SetupLocalHost(ipAddress=baseAddress)

#--- ML Based Experiment

# Setup the learner
learner = learners.Learner('{}./learners/congestion_control_manager/congestion_control_manager.py'.format(DirOffset))

serverNode.AddApplication(learner.ToArgs())

serverNode.AddApplication(['iperf', '-s'])

node.AddApplication(apps.PrepWrapperCall('{}apps/Iperf.py'.format(DirOffset), ['-c', serverNode.IpAddress, '-P', '1', '-t', '10'], 100000, 'http://{}:{}'.format(serverNode.IpAddress, learner.LearnerPort)))

network = networks.NetworkModule(nodes=[serverNode, node])

exps.runExperimentUsingFramework(network, 60)

#--- Benchmarking Experiments

for idx, verPattern in enumerate(VerificationPatternFiles):
    print('Testing with Pattern {}'.format(verPattern))

    serverNode.Applications = []
    node.Applications = []

    learner = learners.Learner('{}./learners/congestion_control_manager/congestion_control_manager.py'.format(DirOffset)
                    , training=2
                    , traceFilePostFix='pattern-{}'.format(idx)
                    , miscArgs=[verPattern])

    serverNode.AddApplication(learner.ToArgs())
    serverNode.AddApplication(['iperf', '-s'])
    node.AddApplication(apps.PrepWrapperCall('{}apps/Iperf.py'.format(DirOffset),
                                             ['-c', serverNode.IpAddress, '-P', '1', '-t', '4000'], 100000,
                                             'http://{}:{}'.format(serverNode.IpAddress, learner.LearnerPort)))

    exps.runExperimentUsingFramework(network, 60)

network.Shutdown()
