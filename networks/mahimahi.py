import subprocess

if __name__ == '__main__':
    print('Special imports')
    import sys
    import os
    sys.path.insert(0, os.getcwd())
    sys.path.insert(0, '../')

import networks.common
import applications.daemon_server


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


def SetupMahiMahiNode(mmShellsList, runOperationServerToo=True, opServerPort=8081, dirOffset='./'):
    """
        Note: If 2 or more shells, IP address is not useful, so Proc must be used, but that also means the operation server cannot run too
    :param mmShellsList:
    :return:
    """

    mmCommands = []

    for shell in mmShellsList:

        mmCommands.extend(shell.CreateArgsList())

    # Default MahiMahi IP address
    daemonPort = opServerPort

    ipAddress = None

    if runOperationServerToo and len(mmShellsList) <= 1:
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

        mmProc.wait()

        # add the operation server command
        mmCommands.extend(applications.daemon_server.PrepareServerArgs(dirOffset=dirOffset, opServerPort=opServerPort))

    # run actual time to finish
    mmProc = subprocess.Popen(mmCommands,
                              stdout=subprocess.PIPE,
                              stdin=subprocess.PIPE,
                              stderr=subprocess.STDOUT,
                              universal_newlines=True)

    print('MM Node {} {} Setup'.format(ipAddress, daemonPort))

    return networks.common.Node(ipAddress=ipAddress, nodeProc=mmProc, daemonPort=daemonPort)


# https://eli.thegreenplace.net/2017/interacting-with-a-long-running-child-process-in-python/
# https://stackoverflow.com/questions/22163422/using-python-to-open-a-shell-environment-run-a-command-and-exit-environment

if __name__ == '__main__':

    node = SetupMahiMahiNode([MahiMahiDelayShell(delayMS=10), MahiMahiDelayShell(delayMS=10)], dirOffset='../', runOperationServerToo=False)

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