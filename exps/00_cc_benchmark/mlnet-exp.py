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

#--- Benchmarking Experiments

# Build the environment
mmShells = list()

mmShells.append(networks.mahimahi.MahiMahiDelayShell(25))
mmShells.append(
    networks.mahimahi.MahiMahiLinkShell(upLinkTraceFilePath='./mahimahi-traces/const48.mahi', downLinkTraceFilePath='./mahimahi-traces/const48.mahi'
                                        , uplinkQueue='droptail', uplinkQueueArgs='packets=400'
                                        , downlinkQueue='droptail', downlinkQueueArgs='packets=400',
                                        uplinkLogFilePath='./tmp/{}-up-log'.format('vegas')))

node, baseAddress = networks.mahimahi.SetupMahiMahiNode(mmShells, dirOffset=DirOffset)

serverNode = networks.SetupLocalHost(ipAddress=baseAddress)

learner = learners.Learner('{}./learners/logging_only_manager/logging_only_manager.py'.format(DirOffset)
                , training=2
                , traceFilePostFix='pattern-{}'.format('vegas')
                , miscArgs=['./input-s-vegas-pattern.csv'])

serverNode.AddApplication(learner.ToArgs())
serverNode.AddApplication(['iperf', '-s'])
node.AddApplication(apps.Iperf.PrepIperfCall(serverNode.IpAddress, serverNode.IpAddress, learner.LearnerPort, 1, 3700, 'vegas'))

network = networks.NetworkModule(nodes=[serverNode, node])

exps.runExperimentUsingFramework(network, 4000)

network.Shutdown()
