import requests
import json
import sys
import subprocess
import time


def UpdateArgs(oldArgs:dict, newArgs:dict):
    """Update the command line args with new args, will replace any matches and add missing"""
    updatedArgs = oldArgs.copy()

    if isinstance(newArgs, dict):

        for key in newArgs.keys():
            updatedArgs[key] = newArgs[key]

    return updatedArgs


def ToCLIArgs(argList:list) -> str:
    """Returns a string of list elements"""
    return ' '.join(argList)


def ToPopenArgs(argDict:dict, replacer:str='~') -> list:
    """Takes the current args, and converts it to a list of commands suitable for a Popen command call. Any args with the key ! instead of - will have only the value passed."""

    # Formatted as ['argName', 'argVal']
    cmdList = list()
    print(argDict)

    for idx, arg in enumerate(argDict.keys()):

        if replacer not in arg:
            cmdList.append(arg)

        argVal = argDict[arg]

        if argVal is not None:
            cmdList.append('{}'.format(argVal))

    return cmdList


def PrepWrapperCall(commandFilePath:str, args:list, runcount:int
                    , agentIPAddress:str=None, agentPort:int=None, probeApproach:int=0) -> list:
    """Prepare command args to call and setup the application wrappers from another caller"""
    commands = list()

    commands.append('python3')

    commands.append(commandFilePath)

    for arg in args:
        commands.append('{}'.format(arg))


    commands.append('{}'.format(probeApproach))

    commands.append('{}'.format(runcount))

    commands.append('http://{}:{}'.format(agentIPAddress, agentPort))

    return commands


def ParseDefaultArgs() -> dict:
    """Parse out the basic command line arguements feed into an application wrapper"""

    appArgs = sys.argv[1:len(sys.argv)-3]

    # convert appArgs to a arg dict
    argDict = dict()

    lastArg = None

    for arg in appArgs:
        if ('-' in arg or '~' in arg) and lastArg is None:
            argDict[arg] = None
            lastArg = arg
        elif ('-' not in arg or '~' not in arg) and lastArg is not None:

            try:
                argDict[lastArg] = int(arg)
            except:
                argDict[lastArg] = arg

            lastArg = None

    probingApproach = sys.argv[-3]
    runCount = int(sys.argv[-2])
    endPoint = sys.argv[-1]

    if len(endPoint) == 0:
        endPoint = None

    parsedArgs = {"appArgs": argDict, "currentArgs":argDict.copy(), "agentURL":endPoint, "runCount":runCount, "probeApproach":probingApproach}

    print('App Args full: {}'.format(parsedArgs))

    return parsedArgs


class App(object):

    def __init__(self):
        """The representation of an application's execution"""

    def Run(self, runArgs:dict) -> (dict, list):
        """Run the application and return the metrics it has/collects and the warnings."""
        return NotImplementedError


def SendToLearner(dataDict, learnerTarget, verbose=False) -> dict:
    """Send a python dict of keys/values to a targeted learner host, get back a response"""

    # Send to learner, and get new action
    if verbose:
        print('application sending {}'.format(dataDict))

    # Encode from dict to JSON again
    jsonData = json.dumps(dataDict)

    response = requests.post(learnerTarget, data=jsonData)

    respDict = json.loads(response.content.decode())

    if verbose:
        print('application received {}'.format(respDict))

    return respDict


def RunApplication(application:App):
    """Parse args, run application, send results, handle additional monitoring"""

    args = ParseDefaultArgs()

    retryCount = 3
    retriesRemaining = retryCount
    retryDelay = 1

    fullFailure = False

    # run n times, allows the controller to "explore" the environment
    currentRunNum = 0
    while(currentRunNum < args['runCount']):

        exception = False

        try:

            # If probing approach is passive, start it before the application runs

            result, warnings = application.Run(args['currentArgs'])

            # If probing approach is active, probe AFTER the application has done stuff

            # If probing approach is passive, end it for packaging

            if args['agentURL'] is not None:
                response = SendToLearner(result, args['agentURL'], verbose=True)

                args['currentArgs'] = UpdateArgs(args['currentArgs'], response)

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
                    currentRunNum = args['runCount']
                    raise Exception('Ran out of retries')
            elif fullFailure:
                currentRunNum = args['runCount']
                raise Exception('Closed')
