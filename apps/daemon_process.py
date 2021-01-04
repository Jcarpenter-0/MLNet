import subprocess
import json
import os
import sys
import time
import glob
import shutil

# intended for use by network sims that are not necessarily reachable for the daemon server


def PrepareDaemonArgs(daemonServerWatchFilePath:str, dirOffset='./', batchRate:int=100):
    '''
    Returns list of args for use in Popen()

            Parameters:
                    dirOffset (str): Path to get to the root directory of the project. for python use
                    opServerPort (int): Port to listen for incoming operation calls

            Returns:
                    argList (list): List of args for use in Popen()
    '''
    return ['python3', '{}apps/daemon_process.py'.format(dirOffset), daemonServerWatchFilePath, '{}'.format(batchRate)]


if __name__ == '__main__':

    # List of procs that this daemon is in charge of
    procs = []


    # Load the basic args
    fileInputDir = sys.argv[1]
    batchRate = int(sys.argv[2])

    run = True

    try:

        while(run):

            # Read the input file
            inputFiles = glob.glob(fileInputDir + '*')

            # snap shot of files, attempt to read them in order
            for inputFile in inputFiles:

                inputFP = open(inputFile, 'r')

                command = inputFP.readline()
                #print('Read {}'.format(command))
                inputFP.close()

                command = command.lstrip()

                # erase file for input
                inputFPEraser = open(inputFile, 'w')

                inputFPEraser.flush()
                inputFPEraser.close()

                if 'STOP' in command:
                    print('Stopping Daemon Procs')
                    # Assume its a stop all command
                    for proc in procs:
                        print('Killing Proc')
                        proc.kill()
                        proc.wait()

                elif len(command) > 0:
                    # run new command
                    print('Daemon - New Command')
                    commands = command.split(' ')

                    procs.append(subprocess.Popen(commands))

                # Wait to check again
                time.sleep(batchRate)

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