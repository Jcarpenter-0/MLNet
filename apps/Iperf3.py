import subprocess
import numpy as np
import json
import time

# Setup the dir
DirOffset = '../../'

import os
import sys

sys.path.insert(0, os.getcwd())
sys.path.insert(0, DirOffset)
# Hack for overcoming some dir issues

import apps


def PrepIperfCall(targetIPaddress:str, agentIPAddress:str=None, agentPort:int=None, probingApproach:int=0, parallelTCPConnections:int=None, runDuration:int=None, congestionControl:str=None, iperfRunTimes:int=10000, iperfLogFileName:str=None, iperfPort:int=None, dirOffset='./../../') -> list:

    iperfCommands = ['-c', targetIPaddress]

    if iperfPort is not None:
        iperfCommands.append('-p')
        iperfCommands.append(iperfPort)

    if parallelTCPConnections is not None:
        iperfCommands.append('-P')
        iperfCommands.append(parallelTCPConnections)

    if runDuration is not None:
        iperfCommands.append('-t')
        iperfCommands.append(runDuration)

    if congestionControl is not None:
        iperfCommands.append('-C')
        iperfCommands.append(congestionControl)

    if iperfLogFileName is not None:
        iperfCommands.append('--logfile')
        iperfCommands.append(iperfLogFileName)

    commands = apps.PrepWrapperCall('{}apps/Iperf3.py'.format(dirOffset), iperfCommands, iperfRunTimes, agentIPAddress, agentPort, probeApproach=probingApproach)
    return commands


def getCC() -> str:

    ccsRaw = subprocess.check_output(['sysctl', 'net.ipv4.tcp_congestion_control'])

    ccsRaw = ccsRaw.decode()

    # net.ipv4.tcp_congestion_control = cubic
    ccRawPieces = ccsRaw.split('=')[-1]

    ccRawPieces = ccRawPieces.lstrip()

    ccRawPieces = ccRawPieces.replace('\n', '')

    return ccRawPieces


def getCCs() -> list:

    ccsRaw = subprocess.check_output(['sysctl', 'net.ipv4.tcp_available_congestion_control'])

    ccsRaw = ccsRaw.decode()

    # example result: net.ipv4.tcp_available_congestion_control = reno cubic
    ccRawPieces = ccsRaw.split('=')[-1]

    ccRawPieces = ccRawPieces.lstrip()

    currentCongestionControlFlavors = ccRawPieces.split(' ')

    return currentCongestionControlFlavors


def test():

    return ''

class Iperf3App(apps.App):

    def ParseOutput(self, rawData: bytes, args: dict) -> dict:

        outputRaw = rawData.decode()

        # get output from the logfile
        if '--logfile' in args.keys():
            logFileFP = open(args['--logfile'], 'r')
            output = json.load(logFileFP)
            logFileFP.close()
        else:
            output = json.loads(outputRaw)

        dataDict = dict()

        startSection = output['start']

        dataDict['host'] = startSection['connecting_to']['host']
        dataDict['port'] = startSection['connecting_to']['port']
        dataDict['version'] = startSection['version']
        dataDict['time'] = "{}".format(startSection['timestamp']['time'])
        dataDict['timesecs'] = startSection['timestamp']['timesecs']
        dataDict['tcp_mss_default'] = startSection['tcp_mss_default']

        dataDict['protocol'] = startSection['test_start']['protocol']
        dataDict['num_streams'] = startSection['test_start']['num_streams']
        dataDict['blksize'] = startSection['test_start']['blksize']
        dataDict['omit'] = startSection['test_start']['omit']
        dataDict['duration'] = startSection['test_start']['duration']
        dataDict['bytes'] = startSection['test_start']['bytes']
        dataDict['blocks'] = startSection['test_start']['blocks']
        dataDict['reverse'] = startSection['test_start']['reverse']

        endSection = output['end']

        sendSection = endSection['sum_sent']

        dataDict['sender-seconds'] = sendSection['seconds']
        dataDict['sender-bytes'] = sendSection['bytes']
        dataDict['sender-bps'] = sendSection['bits_per_second']
        dataDict['sender-retransmits'] = sendSection['retransmits']

        recSection = endSection['sum_received']

        dataDict['receiver-seconds'] = recSection['seconds']
        dataDict['receiver-bytes'] = recSection['bytes']
        dataDict['receiver-bps'] = recSection['bits_per_second']

        # Stream dissection
        streamSection = endSection['streams']

        minRTTs = []
        maxRTTs = []
        avgRTTs = []

        maxSendCWNDs = []

        for stream in streamSection:
            streamSender = stream['sender']

            snd = int(streamSender['max_snd_cwnd'])
            maxSendCWNDs.append(snd)

            # RTTs are in usec (microseconds)
            maxRTT = int(streamSender['max_rtt'])
            maxRTTs.append(maxRTT)

            minRTT = int(streamSender['min_rtt'])
            minRTTs.append(minRTT)

            meanRTT = int(streamSender['mean_rtt'])
            avgRTTs.append(meanRTT)

        # Calculate macros
        dataDict['maxRTT'] = float(np.mean(maxRTTs))
        dataDict['minRTT'] = float(np.mean(minRTTs))
        dataDict['meanRTT'] = float(np.mean(avgRTTs))
        dataDict['max_snd_cwnd'] = int(np.max(maxSendCWNDs))
        dataDict['avg_snd_cwnd'] = float(np.mean(maxSendCWNDs))
        dataDict['min_snd_cwnd'] = int(np.min(maxSendCWNDs))

        dataDict['system_info'] = "\"{}\"".format(startSection['system_info'])

        return dataDict

    def Run(self, runArgs:dict) -> (dict, list):

        # check if outputing to log file, if so must do indexing to prevent overwrites
        if '--logfile' in runArgs.keys():
            runArgs['--logfile'] = runArgs['--logfile']

        cmdArgs = apps.ToPopenArgs(runArgs)

        command = ['iperf3']
        command.extend(cmdArgs)

        # output to Json for easier parsing
        if '-J' not in command:
            command.append('-J')

        outputRaw = subprocess.check_output(command, stderr=subprocess.STDOUT)

        output = self.ParseOutput(outputRaw, runArgs)

        # Add the action args
        output.update(runArgs)

        if '-C' not in command:
            output['-C'] = getCC()

        return output, []


# Allow call to just run iperf with initial args
if __name__ == '__main__':

    apps.RunApplication(Iperf3App())

