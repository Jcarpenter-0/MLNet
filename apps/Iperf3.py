import numpy as np
import subprocess

# Setup the dir
DirOffset = '../../'

import os
import sys
sys.path.insert(0, os.getcwd())
sys.path.insert(0, DirOffset)

import subprocess
import json

import apps


def DefineMetrics() -> dict:
    """Defines what metrics this application provides. Result is dict with metric name and metric info."""
    metricDict = dict()

    metricDict['host'] = str
    metricDict['port'] = int
    metricDict['version'] = str
    metricDict['system_info'] = str
    metricDict['time'] = str
    metricDict['timesecs'] = int
    metricDict['tcp_mss_default'] = int

    metricDict['protocol'] = str
    metricDict['num_streams'] = int
    metricDict['blksize'] = int
    metricDict['omit'] = int
    metricDict['duration'] = int
    metricDict['bytes'] = int
    metricDict['blocks'] = int
    metricDict['reverse'] = int

    metricDict['sender-seconds'] = float
    metricDict['sender-bytes'] = int
    metricDict['sender-bps'] = float
    metricDict['sender-retransmits'] = int

    metricDict['receiver-seconds'] = float
    metricDict['receiver-bytes'] = float
    metricDict['receiver-bps'] = float

    return metricDict


def __getCC() -> str:

    ccsRaw = subprocess.check_output(['sysctl', 'net.ipv4.tcp_congestion_control'])

    ccsRaw = ccsRaw.decode()

    # net.ipv4.tcp_congestion_control = cubic
    ccRawPieces = ccsRaw.split('=')[-1]

    ccRawPieces = ccRawPieces.lstrip()

    ccRawPieces = ccRawPieces.replace('\n', '')

    return ccRawPieces


def __getCCs() -> list:

    ccsRaw = subprocess.check_output(['sysctl', 'net.ipv4.tcp_available_congestion_control'])

    ccsRaw = ccsRaw.decode()

    # example result: net.ipv4.tcp_available_congestion_control = reno cubic
    ccRawPieces = ccsRaw.split('=')[-1]

    ccRawPieces = ccRawPieces.lstrip()

    currentCongestionControlFlavors = ccRawPieces.split(' ')

    return currentCongestionControlFlavors


def ParseOutput(rawData:bytes) -> dict:

    outputRaw = rawData.decode()

    output = json.loads(outputRaw)

    dataDict = dict()

    startSection = output['start']

    dataDict['host'] = startSection['connecting_to']['host']
    dataDict['port'] = startSection['connecting_to']['port']
    dataDict['version'] = startSection['version']
    dataDict['system_info'] = startSection['system_info']
    dataDict['time'] = startSection['timestamp']['time']
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

    return dataDict


def __runIperf3(args:dict) -> dict:

    cmdArgs = apps.ToPopenArgs(args)

    command = ['iperf3']
    command.extend(cmdArgs)

    # Quiet the output for easier parsing
    if '-J' not in command:
        command.append('-J')

    print(command)

    outputRaw = subprocess.check_output(command)

    output = ParseOutput(outputRaw)

    # Add the action args
    output.update(args)

    if '-C' not in command:
        output['-C'] = __getCC()

    return output


# Allow call to just run iperf with initial args
if __name__ == '__main__':

    argDict, endpoint, runcount = apps.ParseDefaultArgs()

    currentArgs = argDict.copy()

    # run n times, allows the controller to "explore" the environment
    for runNum in range(0, runcount):

        result = __runIperf3(currentArgs)

        print(result)

        if endpoint is not None:
            response = apps.SendToLearner(result, endpoint, verbose=True)

            currentArgs = apps.UpdateArgs(currentArgs, response)
