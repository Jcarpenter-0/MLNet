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
import glob
import apps.Iperf3
import exps

testDuration = 3400
testFloat = testDuration + int(testDuration * 0.25)

# Eval the performance of the different CCs on the shared environment
validationPatterns = glob.glob('./input-patterns/*.csv')

try:

    for pattern in validationPatterns:

        patternName = pattern.split('/')[-1].split('.')[0]

        mmShells = list()

        mmShells.append(networks.mahimahi.MahiMahiDelayShell(25))
        mmShells.append(
            networks.mahimahi.MahiMahiLinkShell(upLinkTraceFilePath='../00_cc_benchmark/mahimahi-traces/const48.mahi'
                                                , downLinkTraceFilePath='../00_cc_benchmark/mahimahi-traces/const48.mahi'
                                                , uplinkQueue='droptail', uplinkQueueArgs='packets=400'
                                                , downlinkQueue='droptail', downlinkQueueArgs='packets=400',
                                                uplinkLogFilePath='./tmp/{}-up-log'.format(patternName)))

        node, baseAddress = networks.mahimahi.SetupMahiMahiNode(mmShells, dirOffset=DirOffset)

        serverNode = networks.SetupLocalHost(ipAddress=baseAddress)

        learner = learners.Learner('{}./learners/tcp-flavor-selection/tcp-flavor-selection.py'.format(DirOffset)
                        , learnerDir='./tmp/mm-iperf-benchmark/'
                        , training=2
                        , traceFilePostFix=patternName
                        , miscArgs=[pattern])

        serverNode.AddApplication(learner.ToArgs())
        serverNode.AddApplication(['iperf3', '-s'])
        node.AddApplication(apps.Iperf3.PrepIperfCall(serverNode.IpAddress, serverNode.IpAddress, learner.LearnerPort, 1, 10))

        network1 = networks.NetworkModule(nodes=[serverNode, node])

        exps.runExperimentUsingFramework(network1, testFloat)

        network1.Shutdown()

except Exception as ex:
    print(ex)
finally:
    if network1 is not None:
        network1.Shutdown()