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
import apps.browser_selenium_firefox
import apps.abr_client_dash
import apps.http_server_apache
import exps

# Chrome Browser, running JS DASH video player served from an HTTP web server (apache) over a link of some capacity

overalRepeats = 48
testRepeats = 1
testDuration = 280 * testRepeats
testFloat = int(testDuration + (testDuration * 0.15))
benchMarkAbrs = ['RL']
app = ['firefox', 'chrome']
trainingApps = [app[0], app[1]]


try:

    # do initial training for RL
    if 'RL' in benchMarkAbrs:

        for trainingApp in trainingApps:

            # Build the environment
            mmShells = list()

            mmShells.append(networks.mahimahi.MahiMahiDelayShell(40))

            node, baseAddress, _ = networks.mahimahi.SetupMahiMahiNode(mmShells, dirOffset=DirOffset)

            serverNode = networks.SetupLocalHost(ipAddress=baseAddress)

            learner = agents.framework_AgentServer.AgentWrapper('{}./agents/adaptive_bit_rate_manager/abr_{}.py'.format(DirOffset, 'RL')
                                                                , traceFilePostFix='-{}-{}-training'.format('RL', trainingApp)
                                                                , training=1
                                                                , agentPort=8333)

            serverNode.AddApplication(learner.ToArgs())

            # Setup the web server, put dash.js and the video content in it
            # targets POST localhost:8333
            # Build the custom dash client
            apps.abr_client_dash.MakeCustomDashClient(serverNode.IpAddress, learner.LearnerPort,
                                                      '../05_abr_benchmark/video_server/dash.all.min.js',
                                                      '{}apps/abr_client_dash/dash.all.min.js'.format(DirOffset))

            serverNode.AddApplication(apps.http_server_apache.PrepCall('../05_abr_benchmark/video_server/'))

            # Setup the browser, note, the Browser does not contact the learner, the dash client running inside of it does
            if 'firefox' in trainingApp:
                node.AddApplication(
                    apps.browser_selenium_firefox.PrepCall(
                        'http://' + serverNode.IpAddress + ':80' + '/myindex_{}.html'.format('RL'), testDuration,
                        testRepeats, None, None))
            else:
                node.AddApplication(
                    apps.browser_selenium_chrome.browser_selenium_chrome.PrepCall(
                        'http://' + serverNode.IpAddress + ':80' + '/myindex_{}.html'.format('RL'), testDuration,
                        testRepeats, None, None))

            network = networks.NetworkModule(nodes=[serverNode, node])

            exps.runExperimentUsingFramework(network, testFloat)

            network.Shutdown()


    for idx in range(0, overalRepeats):

        for application in app:

            for abr in benchMarkAbrs:

                # Build the environment
                mmShells = list()

                mmShells.append(networks.mahimahi.MahiMahiDelayShell(40))

                node, baseAddress, _ = networks.mahimahi.SetupMahiMahiNode(mmShells, dirOffset=DirOffset)

                serverNode = networks.SetupLocalHost(ipAddress=baseAddress)

                learner = agents.framework_AgentServer.AgentWrapper('{}./agents/adaptive_bit_rate_manager/abr_{}.py'.format(DirOffset, abr)
                                                                    , traceFilePostFix='-{}-{}-testing'.format(abr, application)
                                                                    , training=0
                                                                    , agentPort=8333)

                serverNode.AddApplication(learner.ToArgs())

                # Setup the web server, put dash.js and the video content in it
                # targets POST localhost:8333
                # Build the custom dash client
                apps.abr_client_dash.MakeCustomDashClient(serverNode.IpAddress, learner.LearnerPort, '../05_abr_benchmark/video_server/dash.all.min.js', '{}apps/abr_client_dash/dash.all.min.js'.format(DirOffset))

                serverNode.AddApplication(apps.http_server_apache.PrepCall('../05_abr_benchmark/video_server/'))

                # Setup the browser, note, the Browser does not contact the learner, the dash client running inside of it does
                if 'firefox' in app:
                    node.AddApplication(
                        apps.browser_selenium_firefox.PrepCall('http://' + serverNode.IpAddress + ':80' + '/myindex_{}.html'.format(abr), testDuration, testRepeats, None, None))
                else:
                    node.AddApplication(
                        apps.browser_selenium_chrome.browser_selenium_chrome.PrepCall('http://' + serverNode.IpAddress + ':80' + '/myindex_{}.html'.format(abr), testDuration, testRepeats, None, None))

                network = networks.NetworkModule(nodes=[serverNode, node])

                exps.runExperimentUsingFramework(network, testFloat)

                network.Shutdown()

except Exception as ex:
    print(ex)
finally:
    try:
        if network is not None:
            network.Shutdown()
    except:
        pass
