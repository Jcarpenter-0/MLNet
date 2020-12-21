if __name__ == '__main__':
    # Setup the dir
    DirOffset = '../../'

    import os
    import sys
    sys.path.insert(0, os.getcwd())
    sys.path.insert(0, DirOffset)

import networks.mahimahi
import learners.common
import apps.Iperf3
import exps

# Testing Macro Settings
VerificationPatternFiles = ['./bbr-pattern.csv', './cubic-pattern.csv', './reno-pattern.csv', './vegas-pattern.csv']


# Setup the learner
learner = learners.common.Learner('{}./learners/congestion_control_manager/congestion_control_manager.py'.format(DirOffset))

# Build the environment
serverNode = networks.SetupLocalHost(interfaceIPSource='enp0s25')

serverNode.AddApplication(['iperf3', '-s'])

mmShells = []

mmShells.append(networks.mahimahi.MahiMahiDelayShell(25))
mmShells.append(networks.mahimahi.MahiMahiLinkShell(upLinkLogFilePath='./const48.mahi', downLinkLogFilePath='./const48.mahi'
                                                    , uplinkQueue='droptail', uplinkQueueArgs='packets=2000'
                                                    , downlinkQueue='droptail', downlinkQueueArgs='packets=2000'))

node = networks.mahimahi.SetupMahiMahiNode(mmShells)

node.AddApplication(apps.PrepWrapperCall('{}apps/Iperf3.py'.format(DirOffset), ['-c', serverNode.IpAddress], 100000, 'http://{}:{}'.format(serverNode.IpAddress, learner.LearnerPort)))

network = networks.NetworkModule(nodes=[serverNode, node])

exps.runExperimentUsingFramework(network, [learner], 35060)

# run a pattern test
print('Testing')
for verPattern in VerificationPatternFiles:
    learner = learners.common.Learner('{}./learners/congestion_control_manager/congestion_control_manager.py'.format(DirOffset)
                    , training=2
                    , traceFilePostFix='pattern-{}'.format(verPattern.replace('.','').replace('/',''))
                    , miscArgs=[verPattern])

    exps.runExperimentUsingFramework(network, [learner], 35060)

network.Shutdown()
