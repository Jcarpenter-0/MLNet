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

# Basic Python Web Server with contents

# Running Parameters
# Web Content Dir
# Port


def PrepCall(webContentDir:str, port:int) -> list:

    return []


def ParseOutput(rawData:bytes, args:dict) -> dict:

    return {}


def __run(args:dict) -> dict:

    cmdArgs = apps.ToPopenArgs(args)

    command = ['python3']
    command.extend(cmdArgs)

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

    return output


if __name__ == '__main__':

    argDict, endpoint, runcount = apps.ParseDefaultArgs()

    currentArgs = argDict.copy()

    retryCount = 3
    retriesRemaining = retryCount
    retryDelay = 1

    fullFailure = False

    debug = False

    if debug:
        procLogFP = open('./node-python-http-c-log.txt'.format(), 'w')
        procLogFP.flush()

    # run n times, allows the controller to "explore" the environment
    currentRunNum = 0
    while (currentRunNum < runcount):

        exception = False

        try:
            if debug:
                procLogFP.write('Pre-Execution done\n'.format())
                procLogFP.flush()

            # check if outputing to log file, if so must do indexing to prevent overwrites
            if '--logfile' in argDict.keys():
                currentArgs['--logfile'] = '{}'.format(currentRunNum) + argDict['--logfile']

            result = __run(currentArgs)

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
