DirOffset = ''
if __name__ == '__main__':
    # Setup the dir
    DirOffset = '../../'

    import os
    import sys
    sys.path.insert(0, os.getcwd())
    sys.path.insert(0, DirOffset)

import networks.mahimahi
import agents.framework_AgentServer
import glob
import apps.Iperf3
import exps

# Scaled agents experiment

testDuration = 3400
testFloat = testDuration + int(testDuration * 0.25)

numberOfActors = 4
actorPattern = './input-patterns/vegas-pattern.csv'
numberOfLearners = 0


try:

    mmShells = list()

    mmShells.append(networks.mahimahi.MahiMahiDelayShell(25))
    mmShells.append(
        networks.mahimahi.MahiMahiLinkShell(upLinkTraceFilePath='../01_cc_benchmark/mahimahi-traces/const48.mahi'
                                            , downLinkTraceFilePath='../01_cc_benchmark/mahimahi-traces/const48.mahi'
                                            , uplinkQueue='droptail', uplinkQueueArgs='packets=400'
                                            , downlinkQueue='droptail', downlinkQueueArgs='packets=400'
                                            ))

    node, baseAddress, _ = networks.mahimahi.SetupMahiMahiNode(mmShells, dirOffset=DirOffset)

    serverNode = networks.SetupLocalHost(ipAddress=baseAddress)

    learnerBasePort = 8080

    for learnerID in range(0, numberOfLearners):

        learner = agents.framework_AgentServer.AgentWrapper('{}./agents/tcp-flavor-selection/tcp-flavor-selection-constrained.py'.format(DirOffset)
                                                            , agentDir='./tmp/learner-{}/'.format(learnerID)
                                                            , agentPort=learnerBasePort + learnerID)

        serverNode.AddApplication(learner.ToArgs())

    for actorID in range(numberOfLearners, numberOfActors):

        learner = agents.framework_AgentServer.AgentWrapper('{}./agents/tcp-flavor-selection/tcp-flavor-selection-constrained.py'.format(DirOffset)
                                                            , agentDir='./tmp/actor-{}/'.format(actorID)
                                                            , agentPort=learnerBasePort + actorID
                                                            , training=2
                                                            , miscArgs=[actorPattern])

        serverNode.AddApplication(learner.ToArgs())

    iperfBasePort = 5201

    for iperfID in range(0, numberOfActors):
        serverNode.AddApplication(['iperf3', '-s', '-p', iperfBasePort + iperfID])

        node.AddApplication(apps.Iperf3.PrepIperfCall(serverNode.IpAddress, serverNode.IpAddress, learnerBasePort + iperfID, parallelTCPConnections=1, runDuration=10, iperfPort=iperfBasePort + iperfID))

    network1 = networks.NetworkModule(nodes=[serverNode, node])

    exps.runExperimentUsingFramework(network1, testFloat)

except Exception as ex:
    print(ex)
finally:
    if network1 is not None:
        network1.Shutdown()

