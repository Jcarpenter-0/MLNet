DirOffset = ''
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
VerificationPatternFiles = []
# './vegas-pattern.csv', './bbr-pattern.csv', './cubic-pattern.csv', './reno-pattern.csv'

# Setup the learner
learner = learners.common.Learner('{}./learners/congestion_control_manager/congestion_control_manager.py'.format(DirOffset))

# Build the environment
mmShells = []

mmShells.append(networks.mahimahi.MahiMahiDelayShell(25))
mmShells.append(networks.mahimahi.MahiMahiLinkShell(upLinkLogFilePath='./const48.mahi', downLinkLogFilePath='./const48.mahi'
                                                    , uplinkQueue='droptail', uplinkQueueArgs='packets=400'
                                                    , downlinkQueue='droptail', downlinkQueueArgs='packets=400'))

node, baseAddress = networks.mahimahi.SetupMahiMahiNode(mmShells, dirOffset=DirOffset)

serverNode = networks.SetupLocalHost(ipAddress=baseAddress)

serverNode.AddApplication(['iperf3', '-s', '-i', '0'])

node.AddApplication(apps.PrepWrapperCall('{}apps/Iperf3.py'.format(DirOffset), ['-c', serverNode.IpAddress, '-P', '1', '-i', '2'], 100000, 'http://{}:{}'.format(serverNode.IpAddress, 8080)))

network = networks.NetworkModule(nodes=[serverNode, node])

exps.runExperimentUsingFramework(network, [learner], 30)

# run a pattern test
for idx, verPattern in enumerate(VerificationPatternFiles):
    print('Testing with Pattern {}'.format(idx))
    learner = learners.common.Learner('{}./learners/congestion_control_manager/congestion_control_manager.py'.format(DirOffset)
                    , training=2
                    , traceFilePostFix='pattern-{}'.format(idx)
                    , miscArgs=[verPattern])

    exps.runExperimentUsingFramework(network, [learner], 120, appNodeServerCooldown=5)


network.Shutdown()
