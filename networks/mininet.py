import apps.framework_Daemon_process
import apps.framework_Daemon_server
import networks
import subprocess
import time
import os
import netifaces
import shutil

# https://www.saltycrane.com/blog/2009/10/how-capture-stdout-in-real-time-python/
# https://gist.github.com/shreyakupadhyay/84dc75607ec1078aca3129c8958f3683
# https://techandtrains.com/2013/11/24/mininet-host-talking-to-internet/
# https://stackoverflow.com/questions/50421826/connecting-mininet-host-to-the-internet
# http://mininet.org/walkthrough/#interact-with-hosts-and-switches
# https://pypi.org/project/mininet/


class MiniNetTopology:

    def __init__(self, topo:str=None, nodeCount:int=0, switchDensity:int=0, linkType:str= None, delay:int=None, bandwidth:int=None):
        self.TopoName = topo
        self.NodeCount = nodeCount
        self.SwitchDensity = switchDensity
        self.Delay = delay
        self.Bandwidth = bandwidth
        self.Link = linkType

    def GetCLI(self) -> list:

        cmdList = ['sudo', 'mn']

        if self.TopoName is not None:
            cmdList.append('--topo')

            topoArgString = '{}'.format(self.TopoName)

            if self.NodeCount is not None and self.NodeCount > 0:
                topoArgString += ',{}'.format(self.NodeCount)

                if self.SwitchDensity is not None and self.SwitchDensity > 0:
                    topoArgString += ',{}'.format(self.SwitchDensity)

            cmdList.append(topoArgString)

        if self.Link:
            cmdList.append('--link')

            linkArgString = '{}'.format(self.Link)

            if self.Bandwidth is not None:
                linkArgString += ',bw={}'.format(self.Bandwidth)

            if self.Delay is not None:
                linkArgString += ',delay={}ms'.format(self.Delay)

            cmdList.append(linkArgString)

        return cmdList


class MiniNetNetworkModule(networks.Network):

    def __init__(self, networkProcs:list=[], nodes:list=[]):
        super().__init__(networkProcs, nodes)

    def Shutdown(self, killTimeout=2, miniNetCooldown=10):
        """Mininet specific shutdown operation"""
        # Shutdown each node
        for node in self.Nodes:
            node.ShutdownNode(killTimeout)

        # Mininet specifically takes only the "exit" command
        self.NetworkProcs[0].stdin.write('exit\n')
        self.NetworkProcs[0].stdin.flush()
        print('MiniNet: shutdown')
        time.sleep(miniNetCooldown)
        print('MiniNet: Cooled')


def SetupMiniNetNetwork(topology:MiniNetTopology, runDaemonServer:bool=False, daemonPort=8081, dirOffset='./', skipHostPrefix='s', inputDir:str='./daemon-proc-input/mn/', excessiveBlanks:int=30) -> networks.Network:
    """Setup a mininet network"""

    mnCommand = topology.GetCLI()

    print('Mininet: {}'.format(mnCommand))

    mnProc = subprocess.Popen(mnCommand,
                                  stdout=subprocess.PIPE,
                                  stdin=subprocess.PIPE,
                                  stderr=subprocess.STDOUT,
                                  universal_newlines=True)

    line = ''

    blanksRemaining = excessiveBlanks

    # read until end of the setup
    while '*** Starting CLI:' not in line:
        line = mnProc.stdout.readline()

        line = line.lstrip()

        if len(line) == 0:
            blanksRemaining-=1
        else:
            print(line)

        if blanksRemaining <= 0:
            raise Exception("Something failed in MiniNet")

    # get the hosts
    mnProc.stdin.write('nodes\n')
    mnProc.stdin.flush()

    time.sleep(.5)

    # example output:
    #
    # h1 h2 s1

    # Read the two lines that provide the host list
    mnProc.stdout.readline()
    output = mnProc.stdout.readline()

    hostLine = output.lstrip().split('\n')[0]
    hosts = hostLine.split(' ')

    # Get all the nodes' ip addresses
    nodes = []

    print(hosts)

    for hostNum, host in enumerate(hosts):

        if skipHostPrefix not in host:

            hostSpecificDir = None

            # get the ip addresses from the ifconfig for each host
            print('{} ifconfig'.format(host))
            mnProc.stdin.write("{} ifconfig\n".format(host))
            mnProc.stdin.flush()

            time.sleep(.5)

            # example output
            # h1-eth0: flags=4163<UP,BROADCAST,RUNNING,MULTICAST>  mtu 1500
            # inet 10.0.0.1  netmask 255.0.0.0  broadcast 10.255.255.255

            # skip the first line
            o1 = mnProc.stdout.readline()
            output = mnProc.stdout.readline()

            ipLineRaw = output.lstrip().split('\n')[0]
            ipLinePieces = ipLineRaw.split(' ')
            ipAddress = '{}'.format(ipLinePieces[1])

            print("ip address {}".format(ipAddress))

            # read to the end
            line = ''
            while 'lo: flags=73<UP,LOOPBACK,RUNNING>  mtu 65536' not in line:
                line = mnProc.stdout.readline()

            # read past the lo's fields, there should be 8 lines, one can check this by doing ifconfig on a node in mn
            for idx in range(0, 8):
                mnProc.stdout.readline()

            port = None

            if runDaemonServer:
                # run the daemon server
                port = daemonPort
                daemonArgs = apps.framework_Daemon_server.PrepareServerArgs(dirOffset=dirOffset, opServerPort=daemonPort)

                daemonCLIArgs = apps.ToCLIArgs(daemonArgs)

                print('MN run ' + "{} {} &\n".format(host, daemonCLIArgs))
                mnProc.stdin.write("{} {} &\n".format(host, daemonCLIArgs))
                mnProc.stdin.flush()

                time.sleep(.5)

                for idx in range(0, 1):
                    li = mnProc.stdout.readline()
                    print(li)
            else:
                print('Host {} - {}'.format(host, hostNum))
                hostSpecificDir = inputDir + '{}/'.format(hostNum)

                try:
                    os.makedirs(hostSpecificDir)
                except Exception as ex:
                    # erase the existing dirs and remake them
                    shutil.rmtree(hostSpecificDir)
                    os.makedirs(hostSpecificDir)

                # run the daemon proc
                mnProc.stdin.write('{} {} &\n'.format(host, apps.framework_Daemon_process.PrepareDaemonCLI(daemonServerWatchFilePath=hostSpecificDir, dirOffset=dirOffset)))
                mnProc.stdin.flush()
                # Read for backgrounding
                print('MiniNet: Waiting for MN to "background" a component, about 2 seconds')
                time.sleep(2)

                # Send control Echo
                mnProc.stdin.write('sh echo CND--!!\n')
                mnProc.stdin.flush()
                time.sleep(.5)

                controlLine = ''

                while 'CND--!!' not in controlLine:
                    output = mnProc.stdout.readline()
                    controlLine = output
                    print(output)

            nodes.append(networks.Node(ipAddress=ipAddress, daemonPort=port, inputDir=hostSpecificDir))

    return MiniNetNetworkModule(networkProcs=[mnProc], nodes=nodes)


class MiniNetNetwork(networks.NetworkSetup):

    def Setup(self, configs:dict) -> (networks.Network, list, float, list):




        return None, None, None, None
