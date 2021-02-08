import subprocess
import json
import os
import sys
import time
import glob
import shutil

# intended for use by network sims that are not necessarily reachable for the daemon server

def PrepareDaemonCLI(daemonServerWatchFilePath:str, dirOffset='./', batchRate:float=1)->str:
    return 'python3 {}apps/daemon_process.py {} {}'.format(dirOffset, daemonServerWatchFilePath, batchRate)


def PrepareDaemonArgs(daemonServerWatchFilePath:str, dirOffset='./', batchRate:float=1)->list:
    '''
    Returns list of args for use in Popen()

            Parameters:
                    dirOffset (str): Path to get to the root directory of the project. for python use
                    opServerPort (int): Port to listen for incoming operation calls

            Returns:
                    argList (list): List of args for use in Popen()
    '''
    return ['python3', '{}apps/daemon_process.py'.format(dirOffset), daemonServerWatchFilePath, '{}'.format(batchRate)]


def Cleanup(procs:list, fileInputDir:str, ):
    print('Daemon Process: Stopping {} Procs'.format(len(procs)))
    for proc in procs:
        proc.kill()
        proc.wait()
        print('Daemon Process: Proc killed')

    procs.clear()

    # Read the input file
    inputFiles = glob.glob(fileInputDir + '*')

    # snap shot of files, attempt to read them in order
    for inputFile in inputFiles:
        # erase file for input
        inputFPEraser = open(inputFile, 'w')

        inputFPEraser.flush()
        inputFPEraser.close()


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
                inputFP.close()

                command = command.lstrip()

                # erase file for input
                inputFPEraser = open(inputFile, 'w')

                inputFPEraser.flush()
                inputFPEraser.close()

                if 'STOP\n' in command:
                    Cleanup(procs, fileInputDir)

                elif 'EXIT\n' in command:
                    print('Daemon Process: Stopping Process NOTE: THIS IS ONLY FOR NETWORK SHUTDOWN')
                    raise KeyboardInterrupt()
                elif len(command) > 0:
                    # run new command
                    print('Daemon Process: New Command')
                    commands = command.split(' ')

                    procs.append(subprocess.Popen(commands))

                # Wait to check again
                time.sleep(batchRate)

    except KeyboardInterrupt:
        pass
    except EOFError as ex1:
        pass
    except Exception as ex:
        print(ex)
    finally:
        print('Daemon Process: Being killed')
        Cleanup(procs, fileInputDir)
        print('Daemon Process: Clean Up')