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

runCount = int(sys.argv[1])

# Get learner endpoint
learner = sys.argv[2]

# Get initial Iperf args
initialArgs = sys.argv[3].split(' ')

# Convert to args dict
iperfArgsDict = dict()

# Setup the commands
iperfArgsDict['iperf3'] = None

# Parse the initial args to setup the command
for initialIperfArg in initialArgs:
    argPieces = initialIperfArg.split('|')

    para = argPieces[0]
    value = argPieces[1]

    iperfArgsDict[para] = value

# Default CC
iperfArgsDict['-C'] = 'cubic'

# Append the JSON flag
iperfArgsDict['-J'] = None

# Hold the previous action here, but set a default first
prevActionID = 0

# Run multiple times

StartVector = {'bps-0':0, 'retransmits-0':0}

for runNum in range(0, runCount):

    iperfCommand = []

    # Assemble the command for execution from the dict
    for para in iperfArgsDict.keys():
        iperfCommand.append(para)

        if iperfArgsDict[para] is not None:
            iperfCommand.append(iperfArgsDict[para])

    # Run Iperf with initial args
    iperfProcResult = subprocess.check_output(iperfCommand)

    # Get result, decode from JSON to a dict
    iperfProcResult = iperfProcResult.decode()
    iperfProcResultDict = json.loads(iperfProcResult)

    # Prune from the dict what you only want to send
    sendDict = dict()

    sendDict['bps-1'] = iperfProcResultDict['end']['sum_sent']['bits_per_second']
    sendDict['retransmits-1'] = iperfProcResultDict['end']['sum_sent']['retransmits']
    sendDict['bps-0'] = StartVector['bps-0']
    sendDict['retransmits-0'] = StartVector['retransmits-0']

    # Append the actionID of the action taken
    sendDict['actionID'] = prevActionID

    # Encode from dict to JSON again
    jsonData = json.dumps(sendDict)

    # Update the start vector
    StartVector['bps-0'] = sendDict['bps-1']
    StartVector['retransmits-0'] = sendDict['retransmits-1']

    # Send to learner, and get new action
    print('Sending {}'.format(sendDict))

    response = requests.post(learner, data=jsonData)

    respDict = json.loads(response.content.decode())

    # Convert action to paras
    newActionID = int(respDict['actionID'])

    print('Recieved ActionID {}'.format(newActionID))

    if newActionID == 0:
        # cubic
        iperfArgsDict['-C'] = 'cubic'
        prevActionID = 0
    elif newActionID == 1:
        # bbr
        iperfArgsDict['-C'] = 'bbr'
        prevActionID = 1
    elif newActionID == 2:
        # vegas
        iperfArgsDict['-C'] = 'vegas'
        prevActionID = 2
    elif newActionID == 3:
        # reno
        iperfArgsDict['-C'] = 'reno'
        prevActionID = 3
    else:
        # default cubic, for ubuntu environments
        iperfArgsDict['-C'] = 'cubic'
        prevActionID = 0
    print('Prev Action is now {}'.format(prevActionID))