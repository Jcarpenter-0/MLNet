import numpy as np
import subprocess
import os
import shutil
import netifaces

from typing import Tuple

import networks
import apps.framework_Daemon_server
import apps.framework_Daemon_process


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

    def __init__(self, delayMS=0, uplinkLogFilePath:str=None, downLinkLogFilePath:str=None):
        super().__init__()
        self.Command = 'mm-delay'
        self.Args.append(delayMS)

        # Args for logging the per packet data in mm format
        if uplinkLogFilePath is not None:
            self.Args.append('--uplink-log')
            self.Args.append('{}'.format(uplinkLogFilePath))

        if downLinkLogFilePath is not None:
            self.Args.append('--downlink-log')
            self.Args.append('{}'.format(downLinkLogFilePath))


class MahiMahiLossShell(MahiMahiShell):

    def __init__(self, lossPercentage=0.0, linkDirection='uplink', uplinkLogFilePath:str=None, downLinkLogFilePath:str=None):
        super().__init__()
        self.Command = 'mm-loss'
        self.Args.append(linkDirection)
        self.Args.append(lossPercentage)

        # Args for logging the per packet data in mm format
        if uplinkLogFilePath is not None:
            self.Args.append('--uplink-log')
            self.Args.append('{}'.format(uplinkLogFilePath))

        if downLinkLogFilePath is not None:
            self.Args.append('--downlink-log')
            self.Args.append('{}'.format(downLinkLogFilePath))
        
    def GetParaString(self):
        paraString = super(MahiMahiLossShell, self).GetParaString()

        paraString = paraString.replace('.','')

        paraString = paraString.replace('/','')

        return paraString


class MahiMahiLinkShell(MahiMahiShell):

    def __init__(self, upLinkTraceFilePath, downLinkTraceFilePath, uplinkLogFilePath:str=None, downLinkLogFilePath:str=None, uplinkQueue:str=None, uplinkQueueArgs:str=None, downlinkQueue:str=None, downlinkQueueArgs:str=None):
        super().__init__()
        self.Command = 'mm-link'
        self.Args.append(upLinkTraceFilePath)
        self.Args.append(downLinkTraceFilePath)

        if uplinkQueue is not None:
            self.Args.append('--uplink-queue={}'.format(uplinkQueue))

            if uplinkQueueArgs is not None:
                self.Args.append('--uplink-queue-args=\"{}\"'.format(uplinkQueueArgs))

        if downlinkQueue is not None:
            self.Args.append('--downlink-queue={}'.format(downlinkQueue))

            if downlinkQueueArgs is not None:
                self.Args.append('--downlink-queue-args=\"{}\"'.format(uplinkQueueArgs))

        # Args for logging the per packet data in mm format
        if uplinkLogFilePath is not None:
            self.Args.append('--uplink-log')
            self.Args.append('{}'.format(uplinkLogFilePath))

        if downLinkLogFilePath is not None:
            self.Args.append('--downlink-log')
            self.Args.append('{}'.format(downLinkLogFilePath))

    def GetParaString(self):
        paraString = super(MahiMahiLinkShell, self).GetParaString()

        paraString = paraString.replace('.','')

        paraString = paraString.replace('/','')

        return paraString


def SetupMahiMahiNode(mmShellsList, runDaemonServer=False, daemonPort=8081, dirOffset='./../', inputDir:str='./daemon-proc-input/mm/') -> Tuple[networks.Node, str, str]:
    """
        Note: If 2 or more shells, IP address is not useful, so Proc must be used, but that also means the operation server cannot run too
    :param mmShellsList:
    :return generated Node, baseIPaddress, interface for node:
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
        mmCommands.extend(apps.framework_Daemon_server.PrepareServerArgs(dirOffset=dirOffset, opServerPort=daemonPort))
    else:
        # create input dir
        try:
            os.makedirs(inputDir)
        except Exception as ex:
            # erase the existing dirs and remake them
            print('Framework: Mahimahi Daemon Setup: Exception making input dirs, attempting remake')
            shutil.rmtree(inputDir)
            os.makedirs(inputDir)

        # add the proc daemon
        mmCommands.extend(apps.framework_Daemon_process.PrepareDaemonArgs(daemonServerWatchFilePath=inputDir, dirOffset=dirOffset))

    # run actual time to finish
    finalmmProc = subprocess.Popen(mmCommands,
                              #stdout=subprocess.PIPE,
                              stdin=subprocess.PIPE,
                              #stderr=subprocess.STDOUT,
                              universal_newlines=True)

    print('Framework: MM Node http://{}:{}/ - Proc {} {}'.format(ipAddress, daemonPort, finalmmProc.pid, finalmmProc.returncode))

    node = networks.Node(ipAddress=ipAddress, nodeProc=finalmmProc, daemonPort=daemonPort, inputDir=inputDir)

    return node, '100.64.0.1', netifaces.interfaces()[-1]


def ParseMMLogFile(logFilePath:str, timeGrouping:int=0) -> list:
    """Parse a mahimahi format trace"""

    fp = open(logFilePath, 'r')
    logFileLinesRaw = fp.readlines()
    fp.close()

    baseTimestamp = int(logFileLinesRaw[4].split(':')[-1].lstrip())

    packetLogLines = logFileLinesRaw[6:]

    # list of dicts
    outputLines = []

    times = []
    delays = []
    sizes = []

    currentGroupStartTS = 0
    currentGroupSize = 0
    currentGroupDelays = []

    for logLineRaw in packetLogLines:

        logLineRaw = logLineRaw.replace('\n','')

        if '-' in logLineRaw:
            # Delivery success
            linePieces = logLineRaw.split(' ')

            packetTimestamp = int(linePieces[0]) - baseTimestamp

            packetSize = int(linePieces[2])

            # packet delay ms
            packetDelay = int(linePieces[3])

            delays.append(packetDelay)
            sizes.append(packetSize)
            times.append(packetTimestamp)

            # in next group?
            if packetTimestamp >= currentGroupStartTS + timeGrouping and timeGrouping is not 0:
                # output last group
                dataLine = {'timestamp(ms)': '{}'.format(currentGroupStartTS), 'bytes': '{}'.format(currentGroupSize),
                            'delay(ms)': '{}'.format(np.mean(currentGroupDelays))}

                outputLines.append(dataLine)

                currentGroupSize = 0
                currentGroupDelays = []
                currentGroupStartTS += timeGrouping
            elif timeGrouping is 0:
                dataLine = {'timestamp(ms)': '{}'.format(packetTimestamp), 'bytes': '{}'.format(packetSize),
                            'delay(ms)': '{}'.format(packetDelay)}

                outputLines.append(dataLine)

            # in current group
            currentGroupDelays.append(packetDelay)
            currentGroupSize += packetSize

    print('Packet Delay Stats: mean {} min {} max {} std {}'.format(np.mean(delays), np.min(delays), np.max(delays), np.std(delays)))
    print('Total sent: {} Bytes'.format(np.sum(sizes)))

    return outputLines


def ParseMacroMMLogFileToData(logFilePath:str, timeGrouping:int=0) -> list:
    """Parse a mahimahi format trace"""

    fp = open(logFilePath, 'r')
    logFileLinesRaw = fp.readlines()
    fp.close()

    baseTimestamp = int(logFileLinesRaw[4].split(':')[-1].lstrip())

    packetLogLines = logFileLinesRaw[6:]

    times = []
    delays = []
    sizes = []

    currentGroupStartTS = 0
    currentGroupSize = 0
    currentGroupDelays = []

    dataLines = []

    for logLineRaw in packetLogLines:

        logLineRaw = logLineRaw.replace('\n','')

        if '-' in logLineRaw:
            # Delivery success
            linePieces = logLineRaw.split(' ')

            packetTimestamp = int(linePieces[0]) - baseTimestamp

            packetSize = int(linePieces[2])

            # packet delay ms
            packetDelay = int(linePieces[3])

            delays.append(packetDelay)
            sizes.append(packetSize)
            times.append(packetTimestamp)

            # in next group?
            if packetTimestamp >= currentGroupStartTS + timeGrouping and timeGrouping is not 0:
                # output last group
                dataLine = {'timestamp(ms)': '{}'.format(currentGroupStartTS), 'bytes': '{}'.format(currentGroupSize),
                            'delay(ms)': '{}'.format(np.mean(currentGroupDelays))}

                dataLines.append(dataLine)

                currentGroupSize = 0
                currentGroupDelays = []
                currentGroupStartTS += timeGrouping

            # in current group
            currentGroupDelays.append(packetDelay)
            currentGroupSize += packetSize

    return dataLines

# https://eli.thegreenplace.net/2017/interacting-with-a-long-running-child-process-in-python/
# https://stackoverflow.com/questions/22163422/using-python-to-open-a-shell-environment-run-a-command-and-exit-environment
