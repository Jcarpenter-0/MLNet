DirOffset = ''
if __name__ == '__main__':
    # Setup the dir
    DirOffset = '../../'

    import os
    import sys
    sys.path.insert(0, os.getcwd())
    sys.path.insert(0, DirOffset)

import numpy as np
import networks.mahimahi
import agents.framework_AgentServer
import apps.Iperf3
import exps
import tools


# ==============================================
# Establish the ideal TCP CC for these link types, no training here, just running existing algs to establish baselines
# ==============================================


testDuration = 60
testRepetitions = 10
linkDelays = [25]
linkLosses = [0.0]
linkThputs = [48]

testCount = len(linkDelays) * len(linkLosses) * len(linkThputs) * testRepetitions
# Estimate time in hours until test completion
testsTime = testCount * (testDuration * 1.10) / 60 / 60

#input('{} Tests planned: Est {} hour(s). Proceed?'.format(testCount, testsTime))

testID = 0

for testrepID in range(0, testRepetitions):
    for linkDelay in linkDelays:
        for linkLoss in linkLosses:
            for linkTput in linkThputs:

                # Create the environment
                node2, baseAddress, _ = networks.mahimahi.QuickSetupMahiMahiNode(delayMS=linkDelay, lossPercentage=linkLoss, bandwidthMbps=linkTput,
                                                                                 dirOffset=DirOffset)
                node1, _, _ = networks.SetupLocalHost(ipAddress=baseAddress, dirOffset=DirOffset)

                # Setup Agent(s)
                agent = agents.framework_AgentServer.AgentWrapper('{}./agents/tcp-flavor-selection/tcp-flavor-selection.py'.format(DirOffset),
                                                                  agentDir='./tmp/naive/',
                                                                  training=1,
                                                                  logFileName='{}-{}-delay-{}-loss-{}-tput-{}.csv'.format(testID, testrepID, linkDelay, linkLoss, linkTput),
                                                                  )

                # Add the Agent(s) to selected node(s)
                node1.AddApplication(agent.ToArgs())

                # Assign Applications to Node(s)
                node1.AddApplication(['iperf3', '-s'])

                node2.AddApplication(apps.PrepGeneralWrapperCall("./apps/Iperf3.py", targetServerAddress=node1.IpAddress, targetServerPort=5201,
                                                                 agentServerAddress=node1.IpAddress, agentServerPort=agent.LearnerPort))

                # Execute the test
                exps.RunExperimentUsingFramework(networks.Network(nodes=[node1, node2]), testDuration * 1.25, interAppDelay=2)

                testID = testID + 1
