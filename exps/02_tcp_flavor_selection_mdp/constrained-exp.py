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
import apps.Iperf3
import exps

# Experiment to compare results of a naive ML approach (full spectrum of actions) vs an MDP restricted approach (limited actions by state)
# The measures of success are the reward measures compared side by side, and for verification, the side metrics that inform them (mbps, delay)

testDuration = 3400
testFloat = testDuration + int(testDuration * 0.25)


try:

    # MahiMahi - Iperf Test
    mmShells = list()

    mmShells.append(networks.mahimahi.MahiMahiDelayShell(25))
    mmShells.append(
        networks.mahimahi.MahiMahiLinkShell(upLinkTraceFilePath='../00_cc_benchmark/mahimahi-traces/const48.mahi'
                                            , downLinkTraceFilePath='../00_cc_benchmark/mahimahi-traces/const48.mahi'
                                            , uplinkQueue='droptail', uplinkQueueArgs='packets=400'
                                            , downlinkQueue='droptail', downlinkQueueArgs='packets=400',
                                            uplinkLogFilePath='./tmp/{}-up-log'.format("constrained")
                                            ))

    node, baseAddress = networks.mahimahi.SetupMahiMahiNode(mmShells, dirOffset=DirOffset)

    serverNode = networks.SetupLocalHost(ipAddress=baseAddress)

    learner = learners.Learner('{}./learners/tcp-flavor-selection-constrained/tcp-flavor-selection.py'.format(DirOffset)
                    , learnerDir='./tmp/mm-iperf-constrained/')

    serverNode.AddApplication(learner.ToArgs())
    serverNode.AddApplication(['iperf3', '-s'])
    node.AddApplication(apps.Iperf3.PrepIperfCall(serverNode.IpAddress, serverNode.IpAddress, learner.LearnerPort, 1, 10))

    network1 = networks.NetworkModule(nodes=[serverNode, node])

    exps.runExperimentUsingFramework(network1, testFloat)

except Exception as ex:
    print(ex)
finally:
    if network1 is not None:
        network1.Shutdown()
