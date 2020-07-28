# Setup the dir
DirOffset = '../../'

import os
import sys
sys.path.insert(0, os.getcwd())
sys.path.insert(0, DirOffset)

import applications.application_common
import applications.Iperf.Iperf

if __name__ == '__main__':

    # create a pingArgs dictionary so the values can be accessed and edited
    appArgsDict = applications.Iperf.Iperf.ParseSysArgs()

    # Parse the learner target
    try:
        learnerTarget = sys.argv[-1]
    except:
        learnerTarget = None

    runCount = int(sys.argv[-2])

    # Hold the previous action here, but set a default first
    prevActionID = 0
    StartVector = {'bps-0': 0, 'retransmits-0': 0}

    # run n times, allows the controller to "explore" the environment
    for runNum in range(0, runCount):

        print(appArgsDict)

        commandArgs = applications.Iperf.Iperf.ConvertArgsDictToArgsList(appArgsDict)

        result = applications.Iperf.Iperf.RunIperf(commandArgs)

        # add the command inputs to the result
        result.update(appArgsDict)

        # Do filtering before sending to learner
        # Prune from the dict what you only want to send
        sendDict = dict()

        sendDict['bps-1'] = result['end']['sum_sent']['bits_per_second']
        sendDict['retransmits-1'] = result['end']['sum_sent']['retransmits']
        sendDict['bps-0'] = StartVector['bps-0']
        sendDict['retransmits-0'] = StartVector['retransmits-0']
        sendDict['-C'] = result['-C']

        sendDict = applications.Iperf.Iperf.TranslateOutGoing(sendDict)

        # Update the start vector
        StartVector['bps-0'] = sendDict['bps-1']
        StartVector['retransmits-0'] = sendDict['retransmits-1']

        # Send to the learner
        if learnerTarget is not None:
            response = applications.application_common.SendToLearner(sendDict, learnerTarget, verbose=True)

            response = applications.Iperf.Iperf.TranslateIncoming(response)

            # Update args
            for key in response.keys():
                appArgsDict[key] = response[key]
