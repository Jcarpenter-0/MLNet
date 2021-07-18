
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

# Run the benchmarking experiment with different configs, tools, and gather the metrics.
# This shows the ease of using different tools in this framework, but also potentially the differences in how the same metric is computed.

# Compare the results of this experiment to the results of the benchmark experiment
# Specifically compare the metrics provided by X across the environments

testDuration = 160
testFloat = testDuration + int(testDuration * 0.25)

try:

    # MahiMahi - Iperf2 Test
    mmShells = list()

    mmShells.append(networks.mahimahi.MahiMahiDelayShell(25))
    mmShells.append(
        networks.mahimahi.MahiMahiLinkShell(upLinkTraceFilePath='./const48.mahi', downLinkTraceFilePath='./const48.mahi'
                                            , uplinkQueue='droptail', uplinkQueueArgs='packets=400'
                                            , downlinkQueue='droptail', downlinkQueueArgs='packets=400',
                                            uplinkLogFilePath='./tmp/mm-{}-iperf-up-log'.format('vegas')))

    node, baseAddress, _ = networks.mahimahi.SetupMahiMahiNode(mmShells, dirOffset=DirOffset)

    serverNode = networks.SetupLocalHost(ipAddress=baseAddress)

    learner = agents.framework_AgentServer.AgentWrapper('{}./agents/logging_only/logging_only.py'.format(DirOffset)
                                                        , training=2
                                                        , agentDir='./tmp/mm-iperf/'
                                                        , logPath='./tmp/pattern-{}-mm-iperf.csv'.format('vegas'))

    serverNode.AddApplication(learner.ToArgs())
    serverNode.AddApplication(['iperf', '-s'])
    node.AddApplication(apps.Iperf.PrepIperfCall(serverNode.IpAddress, serverNode.IpAddress, learner.LearnerPort, 1, testDuration, 'vegas'))

    network1 = networks.NetworkModule(nodes=[serverNode, node])

    exps.runExperimentUsingFramework(network1, testFloat)

    network1.Shutdown()
    network1 = None

    # MahiMahi Iperf3 Test
    mmShells = list()

    mmShells.append(networks.mahimahi.MahiMahiDelayShell(25))
    mmShells.append(
        networks.mahimahi.MahiMahiLinkShell(upLinkTraceFilePath='./const48.mahi', downLinkTraceFilePath='./const48.mahi'
                                            , uplinkQueue='droptail', uplinkQueueArgs='packets=400'
                                            , downlinkQueue='droptail', downlinkQueueArgs='packets=400',
                                            uplinkLogFilePath='./tmp/mm-{}-iperf3-up-log'.format('vegas')))

    node, baseAddress, _ = networks.mahimahi.SetupMahiMahiNode(mmShells, dirOffset=DirOffset)

    serverNode = networks.SetupLocalHost(ipAddress=baseAddress)

    learner = agents.framework_AgentServer.AgentWrapper('{}./agents/logging_only/logging_only.py'.format(DirOffset)
                                                        , training=2
                                                        , agentDir='./tmp/mm-iperf3/'
                                                        , logPath='./tmp/pattern-{}-mm-iperf3.csv'.format('vegas'))

    serverNode.AddApplication(learner.ToArgs())
    serverNode.AddApplication(['iperf3', '-s'])
    node.AddApplication(apps.Iperf3.PrepIperfCall(serverNode.IpAddress, serverNode.IpAddress, learner.LearnerPort, 1, testDuration, 'vegas'))

    network = networks.NetworkModule(nodes=[serverNode, node])

    exps.runExperimentUsingFramework(network, testFloat)

    network.Shutdown()
    network = None

    # Mininet Iperf
    mnTopo = networks.mininet.MiniNetTopology(linkType='tc', delay=25, bandwidth=48)

    mnNet = networks.mininet.SetupMiniNetNetwork(mnTopo, dirOffset=DirOffset)

    learner = agents.framework_AgentServer.AgentWrapper('{}./agents/logging_only/logging_only.py'.format(DirOffset)
                                                        , training=2
                                                        , agentDir='./tmp/mm-iperf/'
                                                        , logPath='./tmp/pattern-{}-mm-iperf.csv'.format('vegas'))

    mnNet.Nodes[0].AddApplication(learner.ToArgs())
    mnNet.Nodes[0].AddApplication(['iperf', '-s'])

    mnNet.Nodes[-1].AddApplication(apps.Iperf.PrepIperfCall(mnNet.Nodes[0].IpAddress, mnNet.Nodes[0].IpAddress, learner.LearnerPort, 1, testDuration, 'vegas'))

    exps.runExperimentUsingFramework(mnNet, testFloat)

    mnNet.Shutdown()
    mnNet = None

    # MiniNet Iperf3 Test

    mnTopo = networks.mininet.MiniNetTopology(linkType='tc', delay=25, bandwidth=48)

    mnNet = networks.mininet.SetupMiniNetNetwork(mnTopo, dirOffset=DirOffset)

    learner = agents.framework_AgentServer.AgentWrapper('{}./agents/logging_only/logging_only.py'.format(DirOffset)
                                                        , training=2
                                                        , agentDir='./tmp/mm-iperf3/'
                                                        , logPath='./tmp/pattern-{}-mm-iperf3.csv'.format('vegas'))

    mnNet.Nodes[0].AddApplication(learner.ToArgs())
    mnNet.Nodes[0].AddApplication(['iperf3', '-s'])

    mnNet.Nodes[-1].AddApplication(apps.Iperf3.PrepIperfCall(mnNet.Nodes[0].IpAddress, mnNet.Nodes[0].IpAddress, learner.LearnerPort, 1, testDuration, 'vegas'))

    exps.runExperimentUsingFramework(mnNet, testFloat)

    mnNet.Shutdown()
    mnNet = None

except Exception as ex:
    print(ex)
finally:
    try:
        if mnNet is not None:
            mnNet.Shutdown()
    except:
        pass

    try:
        if network is not None:
            network.Shutdown()
    except:
        pass

    try:
        if network1 is not None:
            network1.Shutdown()
    except:
        pass
    print('Test: Networks shutdown')