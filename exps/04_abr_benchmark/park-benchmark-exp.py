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
import apps.browser_selenium_chrome.browser_selenium_chrome
import apps.abr_client_dash
import apps.http_server_apache
import exps

# Replicate the Park/Pensieve ABR experiment
# Chrome Browser, running JS DASH video player served from an HTTP web server (apache) over a link of some capacity

testRepeats = 10
testDuration = 280
testFloat = int(testDuration + (testDuration * 0.15))
benchMarkAbrs = ['BB', 'robustMPC']


for abr in benchMarkAbrs:

    # Build the environment
    mmShells = list()

    mmShells.append(networks.mahimahi.MahiMahiDelayShell(40))

    node, baseAddress = networks.mahimahi.SetupMahiMahiNode(mmShells, dirOffset=DirOffset)

    serverNode = networks.SetupLocalHost(ipAddress=baseAddress)

    learner = learners.Learner('{}./learners/adaptive_bit_rate_manager/abr_bufferbased.py'.format(DirOffset)
                    , training=1
                    , learnerPort=8333)


    serverNode.AddApplication(learner.ToArgs())

    # Setup the web server, put dash.js and the video content in it
    # targets POST localhost:8333
    # Build the custom dash client
    apps.abr_client_dash.MakeCustomDashClient(serverNode.IpAddress, learner.LearnerPort, './video_server/dash.all.min.js', '{}apps/abr_client_dash/dash.all.min.js'.format(DirOffset))

    serverNode.AddApplication(apps.http_server_apache.PrepCall('./video_server/'))

    # Setup the browser
    node.AddApplication(
        apps.browser_selenium_chrome.browser_selenium_chrome.PrepCall('http://' + serverNode.IpAddress + ':80' + '/myindex_{}.html'.format(abr), testDuration, testRepeats, serverNode.IpAddress, learner.LearnerPort))

    network = networks.NetworkModule(nodes=[serverNode, node])

    exps.runExperimentUsingFramework(network, testFloat)

    network.Shutdown()

