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
import applications.Iperf.Iperf

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
StartVector = {'bps-0': 0, 'retransmits-0': 0}

for runNum in range(0, runCount):

    iperfCommand = applications.application_common.ConvertArgDictToArgList(iperfArgsDict)

    # Run Iperf with initial args
    iperfProcResultDict = applications.Iperf.Iperf.RunIperf(iperfCommand)

    # Prune from the dict what you only want to send
    sendDict = dict()

    sendDict['bps-1'] = iperfProcResultDict['end']['sum_sent']['bits_per_second']
    sendDict['retransmits-1'] = iperfProcResultDict['end']['sum_sent']['retransmits']
    sendDict['bps-0'] = StartVector['bps-0']
    sendDict['retransmits-0'] = StartVector['retransmits-0']

    # Send action info
    sendDict = applications.application_common.SetActionBinaries(prevActionID, 4, sendDict)

    # Update the start vector
    StartVector['bps-0'] = sendDict['bps-1']
    StartVector['retransmits-0'] = sendDict['retransmits-1']

    # Convert action to paras
    newActionID = applications.application_common.SendToLearner(sendDict, learner)

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
    elif newActionID == 4:
        iperfArgsDict['-C'] = 'westwood'
        prevActionID = 4
    elif newActionID == 5:
        iperfArgsDict['-C'] = 'lp'
        prevActionID = 5
    elif newActionID == 6:
        iperfArgsDict['-C'] = 'bic'
        prevActionID = 6
    elif newActionID == 7:
        iperfArgsDict['-C'] = 'htcp'
        prevActionID = 7
    elif newActionID == 8:
        iperfArgsDict['-C'] = 'veno'
        prevActionID = 8
    elif newActionID == 9:
        iperfArgsDict['-C'] = 'illinois'
        prevActionID = 9
    else:
        # default cubic, for ubuntu environments
        iperfArgsDict['-C'] = 'cubic'
        prevActionID = 0
    print('Prev Action is now {}'.format(prevActionID))