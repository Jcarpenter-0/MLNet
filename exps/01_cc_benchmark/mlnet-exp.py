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
import apps.Iperf
import exps

#--- Benchmarking Experiments

# Build the environment
mmShells = list()

mmShells.append(networks.mahimahi.MahiMahiDelayShell(25))
mmShells.append(
    networks.mahimahi.MahiMahiLinkShell(upLinkTraceFilePath='./mahimahi-traces/const48.mahi', downLinkTraceFilePath='./mahimahi-traces/const48.mahi'
                                        , uplinkQueue='droptail', uplinkQueueArgs='packets=400'
                                        , downlinkQueue='droptail', downlinkQueueArgs='packets=400',
                                        uplinkLogFilePath='./tmp/{}-up-log'.format('vegas')))

node, baseAddress, _ = networks.mahimahi.SetupMahiMahiNode(mmShells, dirOffset=DirOffset)

serverNode = networks.SetupLocalHost(ipAddress=baseAddress)

learner = agents.framework_AgentServer.AgentWrapper('{}./agents/logging_only/logging_only.py'.format(DirOffset)
                                                    , training=2
                                                    , logPath='./tmp/pattern-{}.csv'.format('vegas'))

serverNode.AddApplication(learner.ToArgs())
serverNode.AddApplication(['iperf', '-s'])
node.AddApplication(apps.Iperf.PrepIperfCall(serverNode.IpAddress, serverNode.IpAddress, learner.LearnerPort, runDuration=3700, congestionControl='vegas'))

network = networks.NetworkModule(nodes=[serverNode, node])

exps.runExperimentUsingFramework(network, 4000)

network.Shutdown()
