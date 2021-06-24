
DirOffset = ''
if __name__ == '__main__':
    # Setup the dir
    DirOffset = '../../'

    import os
    import sys
    sys.path.insert(0, os.getcwd())
    sys.path.insert(0, DirOffset)

import networks.mininet
import networks.mahimahi
import learners
import apps.Iperf
import apps.Iperf3
import exps




# Run several "deterministic" experiments to establish some bounds of natural variation

testDuration = 160
testFloat = testDuration + int(testDuration * 0.25)
testCount = 1

try:

    for testID in range(0, testCount):

        mmShells = list()
        mmShells.append(networks.mahimahi.MahiMahiDelayShell(25))
        mmShells.append(
            networks.mahimahi.MahiMahiLinkShell(upLinkTraceFilePath='./const48.mahi', downLinkTraceFilePath='./const48.mahi'
                                                , uplinkQueue='droptail', uplinkQueueArgs='packets=400'
                                                , downlinkQueue='droptail', downlinkQueueArgs='packets=400',
                                                uplinkLogFilePath='./tmp/mm-{}-iperf-up-log'.format('vegas')))

        node, baseAddress = networks.mahimahi.SetupMahiMahiNode(mmShells, dirOffset=DirOffset)

        serverNode = networks.SetupLocalHost(ipAddress=baseAddress)

        learner = learners.Learner('{}./learners/logging_only_manager/logging_only_manager.py'.format(DirOffset)
                        , training=2
                        , learnerDir='./tmp/mm-iperf/'
                        , traceFilePostFix='pattern-{}-mm-iperf'.format('vegas')
                        , miscArgs=['./vegas-pattern.csv'])

        serverNode.AddApplication(learner.ToArgs())
        serverNode.AddApplication(['iperf', '-s'])
        node.AddApplication(apps.Iperf.PrepIperfCall(serverNode.IpAddress, serverNode.IpAddress, learner.LearnerPort, 1, testDuration, 'vegas'))

        network1 = networks.NetworkModule(nodes=[serverNode, node])

        exps.runExperimentUsingFramework(network1, testFloat)

        network1.Shutdown()
        network1 = None

except Exception as ex:
    print(ex)
finally:
    try:
        if network1 is not None:
            network1.Shutdown()
    except:
        pass
