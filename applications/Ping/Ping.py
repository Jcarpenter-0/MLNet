import sys
import subprocess
import json
import requests

# Setup the dir
DirOffset = '../../'

import os
import sys
sys.path.insert(0, os.getcwd())
sys.path.insert(0, DirOffset)

import applications.application_common


def RunPing(pingArgsList):
    """Run Ping command and return results in Json format"""

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
    returnDict['packetBytes'] = inputLine[3].split('(')[0]
    returnDict['packetBytesActual'] = inputLine[3].split('(')[1].replace(')','')

    packetLine = pingOutputLines[3].split(' ')
    returnDict['packetsTransmitted'] = packetLine[0]
    returnDict['packetsReceived'] = packetLine[3]
    returnDict['packetLoss'] = packetLine[5].replace('%','')
    returnDict['time'] = packetLine[-1]

    statLine = pingOutputLines[4].split(' ')[3].split('/')

    returnDict['rttMin'] = statLine[0]
    returnDict['rttAvg'] = statLine[1]
    returnDict['rttMax'] = statLine[2]
    returnDict['rttMdev'] = statLine[3]

    return returnDict


# Allow call to just run iperf with initial args
if __name__ == '__main__':

    # Parse the args
    pingArgs = sys.argv[1:-2]

    # create a pingArgs dictionary so the values can be accessed and edited
    pingArgsDict = dict()

    lastArg = None

    for pingArg in pingArgs:
        if '-' in pingArg and lastArg is None:
            pingArgsDict[pingArg] = None
        elif '-' not in pingArg and lastArg is not None:
            pingArgsDict[lastArg] = pingArg
            lastArg = None
        elif '-' not in pingArg and lastArg is None:
            pingArgsDict['destination'] = pingArg

    # Parse the learner target
    try:
        learnerTarget = sys.argv[-1]
    except:
        learnerTarget = None

    runCount = int(sys.argv[-2])

    # run n times, allows the controller to "explore" the environment
    for runNum in range(0, runCount):

        result = RunPing(pingArgs)

        # add the command inputs to the result
        result.update(pingArgsDict)

        # Send to the learner
        if learnerTarget is not None:
            response = applications.application_common.SendToLearnerL(result, learnerTarget)

            # Update args
            for key in response.keys():
                pingArgsDict[key] = response[key]

            # rebuild the ping args list using new paras
            pingArgs = []

            for arg in pingArgsDict.keys():
                pingArgs.append(arg)

                if pingArgsDict[arg] is not None:
                    pingArgs.append(pingArgsDict[arg])
