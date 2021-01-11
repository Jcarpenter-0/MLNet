import subprocess
import os
import shutil

from typing import Tuple

import networks
import apps.daemon_server
import apps.daemon_process


def MakeMahiMahiLinkFile(bandwidth:int) -> list:
    """Make a mahimahi link file for use in the mm-link shell. This code is almost verbatim taken from the Park project by MIT."""

    linkLines = []

    lines = bandwidth // 12
    for _ in range(lines):
        linkLines.append('1\n')

    return linkLines


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

    def __init__(self, upLinkLogFilePath, downLinkLogFilePath, uplinkQueue:str=None, uplinkQueueArgs:str=None, downlinkQueue:str=None, downlinkQueueArgs:str=None):
        super().__init__()
        self.Command = 'mm-link'
        self.Args.append(upLinkLogFilePath)
        self.Args.append(downLinkLogFilePath)

        if uplinkQueue is not None:
            self.Args.append('--uplink-queue={}'.format(uplinkQueue))

            if uplinkQueueArgs is not None:
                self.Args.append('--uplink-queue-args=\"{}\"'.format(uplinkQueueArgs))

        if downlinkQueue is not None:
            self.Args.append('--downlink-queue={}'.format(downlinkQueue))

            if downlinkQueueArgs is not None:
                self.Args.append('--downlink-queue-args=\"{}\"'.format(uplinkQueueArgs))



    def GetParaString(self):
        paraString = super(MahiMahiLinkShell, self).GetParaString()

        paraString = paraString.replace('.','')

        paraString = paraString.replace('/','')

        return paraString


def SetupMahiMahiNode(mmShellsList, runDaemonServer=True, daemonPort=8081, dirOffset='./../', inputDir:str='./daemon-proc-input/mm/') -> Tuple[networks.Node, str]:
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
    else:
        # create input dir
        try:
            os.makedirs(inputDir)
        except Exception as ex:
            # erase the existing dirs and remake them
            print('Exception making dirs, attempting remake')
            shutil.rmtree(inputDir)
            os.makedirs(inputDir)

        # add the proc daemon
        mmCommands.extend(apps.daemon_process.PrepareDaemonArgs(daemonServerWatchFilePath=inputDir, dirOffset=dirOffset))

    print(mmCommands)
    # run actual time to finish
    mmProc = subprocess.Popen(mmCommands,
                              #stdout=subprocess.PIPE,
                              stdin=subprocess.PIPE,
                              #stderr=subprocess.STDOUT,
                              universal_newlines=True)

    print('MM Node http://{}:{}/ - {}'.format(ipAddress, daemonPort, mmProc.returncode))

    node = networks.Node(ipAddress=ipAddress, nodeProc=mmProc, daemonPort=daemonPort, inputDir=inputDir)

    return node, '100.64.0.1'


# https://eli.thegreenplace.net/2017/interacting-with-a-long-running-child-process-in-python/
# https://stackoverflow.com/questions/22163422/using-python-to-open-a-shell-environment-run-a-command-and-exit-environment
