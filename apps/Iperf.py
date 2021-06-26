import json
import time
import numpy as np
import subprocess

# Setup the dir
DirOffset = '../../'

import os
import sys
sys.path.insert(0, os.getcwd())
sys.path.insert(0, DirOffset)
# Hack for overcoming some dir issues
# https://serverfault.com/questions/566737/iperf-csv-output-format

import apps


def PrepIperfCall(targetIPaddress:str, agentIPAddress:str=None, agentPort:int=None, probingApproach:int=0, parallelTCPConnections:int=None, runDuration:int=None, congestionControl:str=None, iperfRunTimes:int=10000, iperfPort:int=None) -> list:

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
        iperfCommands.append('-Z')
        iperfCommands.append(congestionControl)

    commands = apps.PrepWrapperCall('{}apps/Iperf.py'.format(DirOffset), iperfCommands, iperfRunTimes, agentIPAddress, agentPort, probeApproach=probingApproach)
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


class IperfApp(apps.App):

    def ParseOutput(self, rawData:bytes) -> dict:

        outputRaw = rawData.decode()

        outputLines = outputRaw.split('\n')

        # Take the sum line
        output = outputLines[-2].split(',')

        dataDict = dict()

        if len(outputRaw) <= 0:
            raise Exception('No Iperf output')

        dataDict['timestamp'] = output[0]
        dataDict['source_addr'] = output[1]
        dataDict['source_port'] = output[2]

        dataDict['dest_addr'] = output[3]
        dataDict['dest_port'] = output[4]

        dataDict['interval'] = output[6]
        dataDict['transferred_bytes'] = int(output[7])
        dataDict['bits_per_second'] = float(output[8])

        return dataDict

    def Run(self, runArgs:dict) -> (dict, list):

        cmdArgs = apps.ToPopenArgs(runArgs)

        command = ['iperf']
        command.extend(cmdArgs)

        # format into csv for easier parsing
        if '-y' not in command:
            command.append('-y')
            command.append('C')

        outputRaw = subprocess.check_output(command)

        output = self.ParseOutput(outputRaw)

        # Add the action args
        output.update(runArgs)

        if '-Z' not in command:
            output['-Z'] = getCC()

        return output


# Allow call to just run iperf with initial args
if __name__ == '__main__':

    apps.RunApplication(IperfApp())

