import subprocess
import json
import os
import sys
import time
import glob
import shutil

# intended for use by network sims that are not necessarily reachable for the daemon server

def PrepareDaemonCLI(daemonServerWatchFilePath:str, dirOffset='./', batchRate:float=0.75)->str:
    return 'python3 {}apps/daemon_process.py {} {}'.format(dirOffset, daemonServerWatchFilePath, batchRate)


def PrepareDaemonArgs(daemonServerWatchFilePath:str, dirOffset='./', batchRate:float=0.75)->list:
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
    batchRate = float(sys.argv[2])
    nodeID = fileInputDir.split('/')[-2]

    debuggingLog = False

    if debuggingLog:
        procLogFP = open('./node-{}-subproc-log.txt'.format(nodeID), 'w')

        procLogFP.write('Batch Rate: {}\n'.format(batchRate))
        procLogFP.flush()

    run = True

    try:

        while(run):

            # Read the input file
            inputFiles = glob.glob(fileInputDir + '*')

            # snap shot of files, attempt to read them in order
            for inputFile in inputFiles:
                inputFP = open(inputFile, 'r')

                commands = inputFP.readlines()
                inputFP.close()

                # erase file for input
                inputFPEraser = open(inputFile, 'w')

                inputFPEraser.flush()
                inputFPEraser.close()

                if debuggingLog:
                    procLogFP.write('Reading: {}\n'.format(inputFile))
                    procLogFP.flush()

                for command in commands:

                    command = command.replace('\n','')
                    command = command.lstrip()

                    if debuggingLog:
                        procLogFP.write('{}\n'.format(command))
                        procLogFP.flush()

                    if 'STOP' in command:
                        Cleanup(procs, fileInputDir)

                    elif 'EXIT' in command:
                        print('Daemon Process: Stopping Process NOTE: THIS IS ONLY FOR NETWORK SHUTDOWN')
                        raise KeyboardInterrupt()
                    elif len(command) > 0:
                        # run new command
                        print('Daemon Process: New Command')
                        argCmds = command.split(' ')

                        newProc = subprocess.Popen(argCmds)
                        procs.append(newProc)

                        if debuggingLog:
                            procLogFP.write('New Sub Proc:{} - {} - {}\n'.format(argCmds, newProc.pid, newProc.returncode))
                            procLogFP.flush()

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

    if debuggingLog:
        procLogFP.flush()
        procLogFP.close()