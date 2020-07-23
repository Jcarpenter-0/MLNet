import sys
import subprocess
import json
import requests


def RunPing(pingArgsList):
    """Run Ping command and return results in Json format"""

    command = ['ping']
    command.extend(pingArgsList)

    if '-q' not in command:
        command.append('-q')

    pingOutput = subprocess.check_output(command)

    # Contact learner endpoint with data from ping
    pingOutput = pingOutput.decode()

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
    returnDict['packetLoss'] = packetLine[5]
    returnDict['time'] = packetLine[-1]

    statLine = pingOutputLines[-1].split(' ')[3].split('/')

    returnDict['rttMin'] = statLine[0]
    returnDict['rttAvg'] = statLine[1]
    returnDict['rttMax'] = statLine[2]
    returnDict['rttMdev'] = statLine[3]

    return returnDict


# Allow call to just run iperf with initial args
if __name__ == '__main__':

    # Parse the args
    pingArgs = sys.argv[1:-1]

    # Parse the learner target
    learnerTarget = sys.argv[-1]

    result = RunPing(pingArgs)
