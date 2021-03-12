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


def PrepIperfCall(targetIPaddress:str, learnerIpAddress:str, learnerPort:int, parallelTCPConnections:int=None, runDuration:int=None, congestionControl:str=None, iperfRunTimes:int=10000) -> list:

    iperfCommands = ['-c', targetIPaddress]

    if parallelTCPConnections is not None:
        iperfCommands.append('-P')
        iperfCommands.append(parallelTCPConnections)

    if runDuration is not None:
        iperfCommands.append('-t')
        iperfCommands.append(runDuration)

    if congestionControl is not None:
        iperfCommands.append('-Z')
        iperfCommands.append(congestionControl)

    commands = apps.PrepWrapperCall('{}apps/Iperf.py'.format(DirOffset), iperfCommands, iperfRunTimes, 'http://{}:{}'.format(learnerIpAddress, learnerPort))
    return commands

def DefineMetrics() -> dict:
    """Defines what metrics this application provides. Result is dict with metric name and metric info."""
    metricDict = dict()

    metricDict['timestamp'] = float
    metricDict['source_addr'] = str
    metricDict['source_port'] = int
    metricDict['dest_addr'] = str
    metricDict['dest_port'] = int
    metricDict['interval'] = int
    metricDict['transferred_bytes'] = int
    metricDict['bits_per_second'] = float

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

    output = outputRaw.split(',')

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


def __runIperf3(args:dict) -> dict:

    cmdArgs = apps.ToPopenArgs(args)

    command = ['iperf']
    command.extend(cmdArgs)

    # format into csv for easier parsing
    if '-y' not in command:
        command.append('-y')
        command.append('C')

    outputRaw = subprocess.check_output(command)

    output = ParseOutput(outputRaw)

    # Add the action args
    output.update(args)

    if '-Z' not in command:
        output['-Z'] = __getCC()

    return output


# Allow call to just run iperf with initial args
if __name__ == '__main__':

    argDict, endpoint, runcount = apps.ParseDefaultArgs()

    currentArgs = argDict.copy()

    retryCount = 0
    retriesRemaining = retryCount
    retryDelay = 1

    fullFailure = False

    # run n times, allows the controller to "explore" the environment
    currentRunNum = 0
    while(currentRunNum < runcount):

        exception = False

        try:
            result = __runIperf3(currentArgs)

            if endpoint is not None:
                response = apps.SendToLearner(result, endpoint)

                currentArgs = apps.UpdateArgs(currentArgs, response)


            currentRunNum += 1

            # Refresh retries
            retriesRemaining = retryCount
        except KeyboardInterrupt as inter:
            raise inter
        except subprocess.CalledProcessError as ex:
            exception = True
            print(ex)

        except Exception as ex1:
            exception = True
            fullFailure = True
            print(ex1)
        finally:

            if exception and not fullFailure:

                if retriesRemaining > 0:
                    time.sleep(retryDelay)
                    print('Retrying')
                    retriesRemaining = retriesRemaining - 1
                else:
                    print('Failure')
                    currentRunNum = runcount
                    raise Exception('Ran out of retries')
            elif fullFailure:
                raise Exception('Closed')

