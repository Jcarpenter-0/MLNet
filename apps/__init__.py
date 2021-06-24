import requests
import json
import sys


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


def ParseDefaultArgs():
    """"""

    appArgs = sys.argv[1:]

    #print("App Args {}".format(appArgs))

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

    # Last two are the learner endpoint and the run count
    runCount = int(sys.argv[-2])
    endPoint = sys.argv[-1]

    probingApproach = None

    if len(endPoint) == 0:
        endPoint = None

    return argDict, argDict.copy(), endPoint, runCount


class App(object):

    def __init__(self):
        """The representation of an application's execution"""

    def Run(self, runArgs:dict) -> (dict, list):
        """Run the application and return the metrics it has/collects and the warnings."""
        return NotImplementedError


def RunApplication(application:App):
    """Run an application"""

    argDict, currentArgs, endpoint, runcount = ParseDefaultArgs()

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

            application.Run(currentArgs)

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

def PrepWrapperCall(commandFilePath:str, args:list, runcount:int, endpoint:str) -> list:

    commands = list()

    commands.append('python3')

    commands.append(commandFilePath)

    for arg in args:
        commands.append('{}'.format(arg))

    commands.append('{}'.format(runcount))

    commands.append(endpoint)

    return commands