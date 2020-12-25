import subprocess
import json
import os
import sys

# intended for use by network sims that are not necessarily reachable for the daemon server

def PrepareDaemonArgs(dirOffset='./'):
    '''
    Returns list of args for use in Popen()

            Parameters:
                    dirOffset (str): Path to get to the root directory of the project. for python use
                    opServerPort (int): Port to listen for incoming operation calls

            Returns:
                    argList (list): List of args for use in Popen()
    '''
    return ['python3', '{}apps/daemon_process.py'.format(dirOffset)]


# this is an interactive process

ProcessArgsFieldLabel = 'args'

# List of procs that this daemon is in charge of
procs = []

try:

    command = input('Command:')

    while command is not None:

        commandDict = json.loads(command)

        if ProcessArgsFieldLabel in commandDict.keys():
            popenCmd = commandDict[ProcessArgsFieldLabel]

            procs.append(subprocess.Popen(popenCmd))
        else:
            # Assume its a stop all command
            for proc in procs:
                print('Killing Proc')
                proc.kill()
                proc.wait()

        # Get next command
        command = input('Command:')

except KeyboardInterrupt:
    print('Ending daemon process')
except EOFError as ex1:
    print('Ending daemon process')
except Exception as ex:
    print(ex)
finally:
    # Kill all the stuff
    for proc in procs:
        proc.kill()
        proc.wait()

    print('Sub Procs killed')