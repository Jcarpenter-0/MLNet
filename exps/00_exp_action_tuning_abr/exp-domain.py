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
import apps.browser_selenium_chrome.browser_selenium_chrome
import apps.abr_client_dash
import apps.http_server_apache
import exps
import numpy as np

# Replicate the Park/Pensieve ABR experiment
# Chrome Browser, running JS DASH video player served from an HTTP web server (apache) over a link of some capacity

# Base time from Pensieve is 280s
testDuration = 195
benchMarkAbrs = ['RL_fair']
# Pensieve repeats the test 10 times
testRepetitions = 10
agentCounts = [1]
linkDelays = [5, 25, 60, 120]
linkLosses = [0.0]
linkThputs = [12, 48, 60, 120]

testCount = len(linkDelays) * len(linkLosses) * len(linkThputs) * testRepetitions * len(benchMarkAbrs)
# Estimate time in hours until test completion
testsTime = testCount * (testDuration + 5) / 60 / 60

#input('{} Tests planned: Est {} hour(s). Proceed?'.format(testCount, testsTime))


for testrepID in range(0, testRepetitions):
    for agentCount in agentCounts:
        for linkDelay in linkDelays:
            for linkLoss in linkLosses:
                for linkTput in linkThputs:
                    for abr in benchMarkAbrs:
                        # Create the environment
                        node2, baseAddress, _ = networks.mahimahi.QuickSetupMahiMahiNode(delayMS=linkDelay, lossPercentage=linkLoss, bandwidthMbps=linkTput,
                                                                                         dirOffset=DirOffset)
                        node1, _, _ = networks.SetupLocalHost(ipAddress=baseAddress, dirOffset=DirOffset)

                        # Setup Agent(s)
                        agent = agents.framework_AgentServer.AgentWrapper('{}./agents/adaptive_bit_rate_manager/abr_{}.py'.format(DirOffset, abr),
                                                                          agentDir='./tmp/domain/',
                                                                          training=0,
                                                                          logFileName='{}-action-{}-delay-{}-loss-{}-tput-{}-agents-{}.csv'.format(testrepID, abr, linkDelay, linkLoss, linkTput, agentCount))

                        # Add the Agent(s) to selected node(s)
                        node1.AddApplication(agent.ToArgs())

                        apps.abr_client_dash.MakeCustomDashClient(node1.IpAddress, agent.LearnerPort,
                                                                  '{}apps/streaming-videos/test-video-1/dash.all.min.js'.format(DirOffset),
                                                                  '{}apps/abr_client_dash/dash.all.min.js'.format(DirOffset))

                        #node1.AddApplication(apps.PrepGeneralWrapperCall('./apps/http_server_apache.py',
                        #                                                 pollRate=testDuration,
                        #                                                 additionalArgs={'-server-dir':'/var/www/html/', '-content-dir':'{}apps/streaming-videos/test-video-1/'.format(DirOffset)}))

                        for agentID in range(0, agentCount):

                            # Setup the browser
                            node2.AddApplication(apps.PrepGeneralWrapperCall('./apps/browser_selenium_firefox.py',
                                                                             targetServerAddress=baseAddress,
                                                                             targetServerPort=80,
                                                                             targetServerPath='myindex_RL.html',
                                                                             runDuration=testDuration
                                                                             ))
                        # Execute the test
                        exps.RunExperimentUsingFramework(networks.Network(nodes=[node1, node2]), testDuration + 5)
