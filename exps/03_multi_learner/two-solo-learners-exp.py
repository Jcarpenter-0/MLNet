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

testDuration = 3400
testFloat = testDuration + int(testDuration * 0.25)


try:

    mmShells = list()

    mmShells.append(networks.mahimahi.MahiMahiDelayShell(25))
    mmShells.append(
        networks.mahimahi.MahiMahiLinkShell(upLinkTraceFilePath='../00_cc_benchmark/mahimahi-traces/const48.mahi'
                                            , downLinkTraceFilePath='../00_cc_benchmark/mahimahi-traces/const48.mahi'
                                            , uplinkQueue='droptail', uplinkQueueArgs='packets=400'
                                            , downlinkQueue='droptail', downlinkQueueArgs='packets=400'
                                            ))

    node, baseAddress = networks.mahimahi.SetupMahiMahiNode(mmShells, dirOffset=DirOffset)

    serverNode = networks.SetupLocalHost(ipAddress=baseAddress)

    learner1 = learners.Learner('{}./learners/congestion_control_manager/congestion_control_manager.py'.format(DirOffset)
                                , learnerDir='./tmp/one-learner/', training=0
                                , traceFilePostFix='-solo-duo')

    learner2 = learners.Learner('{}./learners/congestion_control_manager/congestion_control_manager.py'.format(DirOffset)
                                , learnerDir='./tmp/one-learner-2/'
                                , traceFilePostFix='-solo-duo'
                                , training=0
                                , learnerPort=8081)

    serverNode.AddApplication(learner1.ToArgs())
    serverNode.AddApplication(['iperf3', '-s'])

    serverNode.AddApplication(learner2.ToArgs())
    serverNode.AddApplication(['iperf3', '-s', '-p', '9989'])

    node.AddApplication(apps.Iperf3.PrepIperfCall(serverNode.IpAddress, serverNode.IpAddress, learner1.LearnerPort, parallelTCPConnections=1, runDuration=10))
    node.AddApplication(apps.Iperf3.PrepIperfCall(serverNode.IpAddress, serverNode.IpAddress, iperfPort=9989, learnerPort=learner2.LearnerPort, parallelTCPConnections=1, runDuration=10))

    network1 = networks.NetworkModule(nodes=[serverNode, node])

    exps.runExperimentUsingFramework(network1, testFloat)

except Exception as ex:
    print(ex)
finally:
    if network1 is not None:
        network1.Shutdown()
