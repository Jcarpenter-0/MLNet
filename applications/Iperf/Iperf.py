import sys
import subprocess
import json
import applications.application_common

# Some defines
CCListings = ['reno', 'cubic', 'bbr', 'vegas', 'westwood', 'lp', 'bic', 'htcp', 'veno', 'illinois']


def RunIperf(iperfArgList):
    """Run Ping command and return results in Json format"""

    command = ['iperf3']
    command.extend(iperfArgList)

    if '-J' not in command:
        command.append('-J')

    # Run Iperf with initial args
    proceResult = subprocess.check_output(command)

    # Get result, decode from JSON to a dict
    proceResult = proceResult.decode()

    resultDict = json.loads(proceResult)

    return resultDict


def ParseSysArgs():
    """Take in the sys args (command args) and parse them into a python dict"""
    appArgs = sys.argv[1:-2]

    # create a pingArgs dictionary so the values can be accessed and edited
    appArgsDict = dict()

    lastArg = None

    for arg in appArgs:
        if '-' in arg and lastArg is None:
            appArgsDict[arg] = None
            lastArg = arg
        elif '-' not in arg and lastArg is not None:

            try:
                appArgsDict[lastArg] = int(arg)
            except:
                pass
                appArgsDict[lastArg] = arg

            lastArg = None

    # Default CC, ensure it is set right
    if '-C' not in appArgsDict.keys():
        appArgsDict['-C'] = 'cubic'

    return appArgsDict


def ConvertArgsDictToArgsList(appArgsDict):
    """Convert an python dict of application args into a list for subprocess execution"""
    # rebuild the ping args list using new paras
    args = []

    for arg in appArgsDict.keys():
        args.append(arg)

        if appArgsDict[arg] is not None:
            args.append('{}'.format(appArgsDict[arg]))

    return args


def TranslateIncoming(learnerResponseDict):

    # Translate binary columns for CC into -c para

    # for each CC we could have, find the one that is set to "true"
    for cc in CCListings:
        # check if true
        try:
            if learnerResponseDict[cc] == 1:
                learnerResponseDict['-C'] = cc

            # delete when finished
            del learnerResponseDict[cc]
        except:
            print('Skipping key in incoming')

    return learnerResponseDict

def TranslateOutGoing(appResultsDict):

    # Translate -c congestion control arg into binary columns
    # Get current CC
    currentCC = appResultsDict['-C']

    for cc in CCListings:

        if cc == currentCC:
            appResultsDict[cc] = 1
        else:
            appResultsDict[cc] = 0

    return appResultsDict

# Allow call to just run iperf with initial args
if __name__ == '__main__':

    # create a pingArgs dictionary so the values can be accessed and edited
    appArgsDict = ParseSysArgs()

    # Parse the learner target
    try:
        learnerTarget = sys.argv[-1]
    except:
        learnerTarget = None

    runCount = int(sys.argv[-2])

    # run n times, allows the controller to "explore" the environment
    for runNum in range(0, runCount):

        print(appArgsDict)

        commandArgs = ConvertArgsDictToArgsList(appArgsDict)

        result = RunIperf(commandArgs)

        # add the command inputs to the result
        result.update(appArgsDict)

        result = TranslateOutGoing(result)

        # Send to the learner
        if learnerTarget is not None:
            response = applications.application_common.SendToLearner(result, learnerTarget, verbose=True)

            response = TranslateIncoming(response)

            # Update args
            for key in response.keys():
                appArgsDict[key] = response[key]