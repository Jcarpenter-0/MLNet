import subprocess

# Setup the dir
DirOffset = '../../'

import os
import sys
sys.path.insert(0, os.getcwd())
sys.path.insert(0, DirOffset)

import applications.application_common


def RunPing(pingArgsList):
    """Run Ping command and return results in python Dict"""

    command = ['ping']
    command.extend(pingArgsList)

    if '-q' not in command:
        command.append('-q')

    pingOutput = subprocess.check_output(command)

    # Contact learner endpoint with data from ping
    pingOutput = pingOutput.decode()

    print('Ping Output: {}'.format(pingOutput))

    returnDict = dict()

    # Parse the output
    pingOutputLines = pingOutput.split('\n')

    inputLine = pingOutputLines[0].split(' ')

    returnDict['targetURL'] = inputLine[1]
    returnDict['targetIP'] = inputLine[2]
    returnDict['packetBytes'] = int(inputLine[3].split('(')[0])
    returnDict['packetBytesActual'] = int(inputLine[3].split('(')[1].replace(')',''))

    packetLine = pingOutputLines[3].split(' ')
    returnDict['packetsTransmitted'] = int(packetLine[0])
    returnDict['packetsReceived'] = int(packetLine[3])
    returnDict['packetLoss'] = float(packetLine[5].replace('%', ''))
    returnDict['time'] = int(packetLine[-1].replace('ms', ''))

    statLine = pingOutputLines[4].split(' ')[3].split('/')

    returnDict['rttMin'] = float(statLine[0])
    returnDict['rttAvg'] = float(statLine[1])
    returnDict['rttMax'] = float(statLine[2])
    returnDict['rttMdev'] = float(statLine[3])

    return returnDict


def ParsePingSysArgs():
    """Take in the sys args (command args) and parse them into a python dict"""
    pingArgs = sys.argv[1:-2]

    # create a pingArgs dictionary so the values can be accessed and edited
    pingArgsDict = dict()

    lastArg = None

    for pingArg in pingArgs:
        if '-' in pingArg and lastArg is None:
            pingArgsDict[pingArg] = None
            lastArg = pingArg
        elif '-' not in pingArg and lastArg is not None:

            try:
                pingArgsDict[lastArg] = int(pingArg)
            except:
                pass
                pingArgsDict[lastArg] = pingArg

            lastArg = None
        elif '-' not in pingArg and lastArg is None:
            pingArgsDict['destination'] = pingArg

    return pingArgsDict


def ConvertArgsDictToArgsList(appArgsDict):
    """Convert an python dict of application args into a list for subprocess execution"""
    # rebuild the ping args list using new paras
    args = []

    for arg in appArgsDict.keys():

        if arg != 'destination':
            args.append(arg)

        if appArgsDict[arg] is not None:
            args.append('{}'.format(appArgsDict[arg]))

    return args

# Allow call to just run iperf with initial args
if __name__ == '__main__':

    pingArgsDict = ParsePingSysArgs()

    # Parse the learner target
    try:
        learnerTarget = sys.argv[-1]
    except:
        learnerTarget = None

    runCount = int(sys.argv[-2])

    # run n times, allows the controller to "explore" the environment
    for runNum in range(0, runCount):

        print(pingArgsDict)

        commandArgs = ConvertArgsDictToArgsList(pingArgsDict)

        result = RunPing(commandArgs)

        # add the command inputs to the result
        result.update(pingArgsDict)

        # Send to the learner
        if learnerTarget is not None:
            response = applications.application_common.SendToLearner(result, learnerTarget, verbose=True)

            # Update args
            for key in response.keys():
                pingArgsDict[key] = response[key]
