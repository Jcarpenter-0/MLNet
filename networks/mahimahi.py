import subprocess
import networks
import apps.daemon_server


class MahiMahiShell():

    def __init__(self):
        self.Command = None
        self.Args = []

    def GetParaString(self):
        """Return a string simply describing the shell. Ex: delay-10ms"""
        descString = self.Command

        for arg in self.Args:
            descString += str(arg)

        return descString

    def CreateArgsList(self):
        """

        :return: returns a list of stringified paras for use in Popen()
        """
        commandArgs = [self.Command]

        for arg in self.Args:
            commandArgs.append('{}'.format(arg))

        return commandArgs


class MahiMahiDelayShell(MahiMahiShell):

    def __init__(self, delayMS=0):
        super().__init__()
        self.Command = 'mm-delay'
        self.Args.append(delayMS)


class MahiMahiLossShell(MahiMahiShell):

    def __init__(self, lossPercentage=0.0, linkDirection='uplink'):
        super().__init__()
        self.Command = 'mm-loss'
        self.Args.append(linkDirection)
        self.Args.append(lossPercentage)
        
    def GetParaString(self):
        paraString = super(MahiMahiLossShell, self).GetParaString()

        paraString = paraString.replace('.','')

        paraString = paraString.replace('/','')

        return paraString


class MahiMahiLinkShell(MahiMahiShell):

    def __init__(self, upLinkLogFilePath, downLinkLogFilePath):
        super().__init__()
        self.Command = 'mm-link'
        self.Args.append(upLinkLogFilePath)
        self.Args.append(downLinkLogFilePath)

    def GetParaString(self):
        paraString = super(MahiMahiLinkShell, self).GetParaString()

        paraString = paraString.replace('.','')

        paraString = paraString.replace('/','')

        return paraString


def SetupMahiMahiNode(mmShellsList, runDaemonServer=True, daemonPort=8081, dirOffset='./') -> networks.Node:
    """
        Note: If 2 or more shells, IP address is not useful, so Proc must be used, but that also means the operation server cannot run too
    :param mmShellsList:
    :return:
    """

    mmCommands = []

    for shell in mmShellsList:

        mmCommands.extend(shell.CreateArgsList())

    # Default MahiMahi IP address
    daemonPort = daemonPort

    ipAddress = None

    if runDaemonServer and len(mmShellsList) <= 1:
        # Parse the IP address of the created node
        mmProc = subprocess.Popen(mmCommands,
                                  stdout=subprocess.PIPE,
                                  stdin=subprocess.PIPE,
                                  stderr=subprocess.STDOUT,
                                  universal_newlines=True)

        output, _ = mmProc.communicate("ifconfig\n")

        ipLineRaw = output.lstrip().split('\n')[1]
        ipLinePieces = ipLineRaw.split(' ')
        ipAddress = '{}'.format(ipLinePieces[9])

        # add the operation server command
        mmCommands.extend(apps.daemon_server.PrepareServerArgs(dirOffset=dirOffset, opServerPort=daemonPort))

    # run actual time to finish
    mmProc = subprocess.Popen(mmCommands,
                              stdout=subprocess.PIPE,
                              stdin=subprocess.PIPE,
                              stderr=subprocess.STDOUT,
                              universal_newlines=True)

    print('MM Node {} {} {}'.format(ipAddress, daemonPort, mmProc.returncode))

    return networks.Node(ipAddress=ipAddress, nodeProc=mmProc, daemonPort=daemonPort)


def SetupMahiMahiNetwork(setupArgs:dict) -> networks.NetworkModule:
    """Autobuilder method for creating a mahi mahi network"""




    return None


class MahiMahiNetworkDefinition(networks.__networkDefinition):

    def Setup(self, setupArgs:dict) -> networks.NetworkModule:
        """"""
        return SetupMahiMahiNetwork(setupArgs)



# https://eli.thegreenplace.net/2017/interacting-with-a-long-running-child-process-in-python/
# https://stackoverflow.com/questions/22163422/using-python-to-open-a-shell-environment-run-a-command-and-exit-environment

if __name__ == '__main__':

    print('Special imports')
    import sys
    import os
    sys.path.insert(0, os.getcwd())
    sys.path.insert(0, '../')

    node = SetupMahiMahiNode([MahiMahiDelayShell(delayMS=10), MahiMahiDelayShell(delayMS=10)], dirOffset='../', runDaemonServer=False)

    print(node.IpAddress)
    print(node.NodeProc.returncode)

    # Must run from cmd as from IDE dnsmasq have problems
    #proc = subprocess.Popen(['mm-delay', '40'], stdout=subprocess.PIPE, stdin=subprocess.PIPE, stderr=subprocess.STDOUT, universal_newlines=True)

    # call limited ping
    output, _ = node.NodeProc.communicate("ping 192.168.1.134 -c 2\n")

    print(output)

    # call limited ping again
    node.NodeProc.wait()

    print('Done')