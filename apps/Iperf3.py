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


def PrepIperfCall(targetIPaddress:str, learnerIpAddress:str, learnerPort:int, parallelTCPConnections:int=None, runDuration:int=None, congestionControl:str=None, iperfRunTimes:int=10000, iperfLogFileName:str=None) -> list:

    iperfCommands = ['-c', targetIPaddress]

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

    commands = apps.PrepWrapperCall('{}apps/Iperf3.py'.format(DirOffset), iperfCommands, iperfRunTimes, 'http://{}:{}'.format(learnerIpAddress, learnerPort))
    return commands


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

    metricDict['maxRTT'] = float
    metricDict['minRTT'] = float
    metricDict['meanRTT'] = float
    metricDict['max_snd_cwnd'] = float
    metricDict['avg_snd_cwnd'] = float
    metricDict['min_snd_cwnd'] = float

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


def ParseOutput(rawData:bytes, args:dict) -> dict:

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


def __runIperf3(args:dict) -> dict:

    cmdArgs = apps.ToPopenArgs(args)

    command = ['iperf3']
    command.extend(cmdArgs)

    # output to Json for easier parsing
    if '-J' not in command:
        command.append('-J')

    outputRaw = bytes()

    try:
        outputRaw = subprocess.check_output(command, stderr=subprocess.STDOUT)
    except subprocess.CalledProcessError as ex:
        if debug:
            procLogFP.write('{} - {} - {}\n'.format(ex.returncode, ex.stdout, ex.stderr))
            procLogFP.flush()
    except Exception as ex:
        if debug:
            procLogFP.write('Check Error: {}\n'.format(ex))
            procLogFP.flush()

    if debug:
        procLogFP.write('OutputRaw: {}\n'.format(outputRaw.decode()))
        procLogFP.flush()

    output = ParseOutput(outputRaw, currentArgs)

    # Add the action args
    output.update(args)

    if '-C' not in command:
        output['-C'] = __getCC()

    return output


# Allow call to just run iperf with initial args
if __name__ == '__main__':

    argDict, endpoint, runcount = apps.ParseDefaultArgs()

    currentArgs = argDict.copy()

    retryCount = 3
    retriesRemaining = retryCount
    retryDelay = 1

    fullFailure = False

    debug = False

    if debug:
        procLogFP = open('./node-iperf3-c-log.txt'.format(), 'w')
        procLogFP.flush()

    # run n times, allows the controller to "explore" the environment
    currentRunNum = 0
    while(currentRunNum < runcount):

        exception = False

        try:
            if debug:
                procLogFP.write('Pre-Execution done\n'.format())
                procLogFP.flush()


            # check if outputing to log file, if so must do indexing to prevent overwrites
            if '--logfile' in argDict.keys():
                currentArgs['--logfile'] = '{}'.format(currentRunNum) + argDict['--logfile']

            result = __runIperf3(currentArgs)

            if endpoint is not None:
                response = apps.SendToLearner(result, endpoint, verbose=True)

                if debug:
                    procLogFP.write('One done: {}\n'.format(result))
                    procLogFP.flush()

                currentArgs = apps.UpdateArgs(currentArgs, response)

            currentRunNum += 1

            # Refresh retries
            retriesRemaining = retryCount
        except KeyboardInterrupt as inter:
            raise inter
        except subprocess.CalledProcessError as ex:
            exception = True
            if debug:
                procLogFP.write('{} - {} - {}\n'.format(ex.returncode, ex.stdout, ex.stderr))
                procLogFP.flush()

            print(ex)
        except Exception as ex1:
            exception = True
            fullFailure = True
            print(ex1)
            if debug:
                procLogFP.write('{}\n'.format(ex1))
                procLogFP.flush()
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
                currentRunNum = runcount
                raise Exception('Closed')

    if debug:
        procLogFP.flush()
        procLogFP.close()

