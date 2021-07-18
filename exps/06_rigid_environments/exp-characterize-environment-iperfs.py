
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
import agents.framework_AgentServer
import apps.Iperf
import apps.Iperf3
import exps


# Run several "deterministic" experiments to establish some bounds of natural variation

testDuration = 120
testFloat = testDuration + int(testDuration * 0.25)
testCount = 100
applications = ['iperf', 'iperf3']

print('Test: ~{} hour(s) = ~{} second(s)'.format(testFloat * testCount * len(applications) / 60 / 60, testFloat * testCount * len(applications) ))

try:

    for idx, app in enumerate(applications):

        for testID in range(0, testCount):

            mmShells = list()
            mmShells.append(networks.mahimahi.MahiMahiDelayShell(25))
            mmShells.append(
                networks.mahimahi.MahiMahiLinkShell(upLinkTraceFilePath='./const48.mahi', downLinkTraceFilePath='./const48.mahi'
                                                    , uplinkQueue='droptail', uplinkQueueArgs='packets=400'
                                                    , downlinkQueue='droptail', downlinkQueueArgs='packets=400'
                                                    #uplinkLogFilePath='./tmp/application-dif-{}-up-log-{}'.format(app, testID))
            ))

            node, baseAddress, _ = networks.mahimahi.SetupMahiMahiNode(mmShells, dirOffset=DirOffset)

            serverNode = networks.SetupLocalHost(ipAddress=baseAddress)

            learner = agents.framework_AgentServer.AgentWrapper('{}./agents/logging_only_manager/logging_only_manager.py'.format(DirOffset)
                                                                , training=2
                                                                , agentDir='./tmp/application-dif/'
                                                                , traceFilePostFix='pattern-{}-{}-{}-mm'.format('vegas', app, testID)
                                                                , miscArgs=['./input-patterns/{}-pattern.csv'.format('vegas'), idx])

            serverNode.AddApplication(learner.ToArgs())
            serverNode.AddApplication([app, '-s'])

            if app == 'iperf':
                node.AddApplication(apps.Iperf.PrepIperfCall(serverNode.IpAddress, serverNode.IpAddress, learner.LearnerPort, parallelTCPConnections=1, runDuration=10, congestionControl='vegas'))
            else:
                node.AddApplication(apps.Iperf3.PrepIperfCall(serverNode.IpAddress, serverNode.IpAddress, learner.LearnerPort, parallelTCPConnections=1, runDuration=10, congestionControl='vegas'))

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
