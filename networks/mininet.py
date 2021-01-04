import apps.daemon_process
import apps.daemon_server
import networks
import subprocess
import time
import os
import shutil

# https://www.saltycrane.com/blog/2009/10/how-capture-stdout-in-real-time-python/
# https://gist.github.com/shreyakupadhyay/84dc75607ec1078aca3129c8958f3683
# https://techandtrains.com/2013/11/24/mininet-host-talking-to-internet/
# https://stackoverflow.com/questions/50421826/connecting-mininet-host-to-the-internet

class MiniNetNetworkDefinition(networks.__networkDefinition):

    def Setup(self, setupArgs:dict) -> networks.NetworkModule:
        """Setup a mininet network, this will utilize many assumptions for the sake of speed,
         lower grain functionality is still easily doable via the component pieces."""

        return SetupMiniNetNetwork(setupArgs)


def SetupMiniNetNetwork(setupArgs:dict, runDaemonServer:bool=True, daemonPort=8081, dirOffset='./', skipHostPrefix='s', inputDir:str='./daemon-proc-input/mn/') -> networks.NetworkModule:
    """Setup a mininet network"""

    mnCommand = ['sudo', 'mn']

    mnProc = subprocess.Popen(mnCommand,
                                  stdout=subprocess.PIPE,
                                  stdin=subprocess.PIPE,
                                  stderr=subprocess.STDOUT,
                                  universal_newlines=True)

    line = ''

    # read until end of the setup
    while '*** Starting CLI:' not in line:
        line = mnProc.stdout.readline()

    # get the hosts
    mnProc.stdin.write('nodes\n')
    mnProc.stdin.flush()

    time.sleep(1)

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

    for host in hosts:

        if skipHostPrefix not in host:

            # get the ip addresses from the ifconfig for each host
            print('{} ifconfig'.format(host))
            mnProc.stdin.write("{} ifconfig\n".format(host))
            mnProc.stdin.flush()

            time.sleep(1)

            # example output
            # h1-eth0: flags=4163<UP,BROADCAST,RUNNING,MULTICAST>  mtu 1500
            # inet 10.0.0.1  netmask 255.0.0.0  broadcast 10.255.255.255

            # skip the first line
            o1 = mnProc.stdout.readline()
            print(o1)
            output = mnProc.stdout.readline()
            print(output)

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
                daemonArgs = apps.daemon_server.PrepareServerArgs(dirOffset=dirOffset, opServerPort=daemonPort)

                daemonCLIArgs = apps.ToCLIArgs(daemonArgs)

                print('MN run ' + "{} {} &\n".format(host, daemonCLIArgs))
                mnProc.stdin.write("{} {}\n".format(host, daemonCLIArgs))
                mnProc.stdin.flush()

                time.sleep(1)

                for idx in range(0, 1):
                    li = mnProc.stdout.readline()
                    print(li)
            else:

                try:
                    os.makedirs(inputDir)
                except Exception as ex:
                    # erase the existing dirs and remake them
                    print('Exception making dirs, attempting remake')
                    shutil.rmtree(inputDir)
                    os.makedirs(inputDir)


                # run the daemon proc
                mnProc.stdin.write('{}\n'.format(apps.daemon_process.PrepareDaemonArgs(daemonServerWatchFilePath=inputDir, dirOffset=dirOffset)))
                mnProc.stdin.flush()

            nodes.append(networks.Node(ipAddress=ipAddress, daemonPort=port))

    return networks.NetworkModule(networkProcs=[mnProc], nodes=nodes)


if __name__ == '__main__':
    tst = SetupMiniNetNetwork(dict())
