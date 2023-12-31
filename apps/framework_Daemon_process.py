import subprocess
import json
import os
import sys
import time
import glob
import signal
import shutil

# intended for use by network sims that are not necessarily reachable for the daemon server
# https://stackoverflow.com/questions/18499497/how-to-process-sigterm-signal-gracefully

def PrepareDaemonCLI(daemonServerWatchFilePath:str, dirOffset='./', batchRate:float=0.75)->str:
    return 'python3 {}apps/framework_Daemon_process.py {} {}'.format(dirOffset, daemonServerWatchFilePath, batchRate)


def PrepareDaemonArgs(daemonServerWatchFilePath:str, dirOffset='./', batchRate:float=0.75)->list:
    '''
    Returns list of args for use in Popen()

            Parameters:
                    dirOffset (str): Path to get to the root directory of the project. for python use
                    opServerPort (int): Port to listen for incoming operation calls

            Returns:
                    argList (list): List of args for use in Popen()
    '''
    return ['python3', '{}apps/framework_Daemon_process.py'.format(dirOffset), daemonServerWatchFilePath, '{}'.format(batchRate)]


def Cleanup(procs:list, fileInputDir:str, ):
    print('Daemon Process: Stopping {} Procs'.format(len(procs)))
    for proc in procs:
        proc.terminate()
        proc.kill()
        proc.wait()
        print('Daemon Process: Proc {} - {} - {}'.format(proc.pid, proc.returncode, proc.args))

    procs.clear()

    # Read the input file
    inputFiles = glob.glob(fileInputDir + '*')

    # snap shot of files, attempt to read them in order
    for inputFile in inputFiles:
        # erase file for input
        inputFPEraser = open(inputFile, 'w')

        inputFPEraser.flush()
        inputFPEraser.close()


def test():

    print('TERM TEST')

if __name__ == '__main__':

    # List of procs that this daemon is in charge of
    daemonSubprocesses = []

    # Load the basic args
    fileInputDir = sys.argv[1]
    batchRate = float(sys.argv[2])
    nodeID = fileInputDir.split('/')[-2]

    run = True

    try:

        print('Node {}: Daemon Process: Going up: {} - {}'.format(nodeID, os.getcwd(), sys.argv))

        signal.signal(signal.SIGINT, test)
        signal.signal(signal.SIGTERM, test)

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

                for command in commands:

                    command = command.replace('\n','')
                    command = command.lstrip()

                    if 'STOP' in command:
                        Cleanup(daemonSubprocesses, fileInputDir)

                    elif 'EXIT' in command:
                        print('Node {}: Daemon Process: Stopping Process NOTE: THIS IS ONLY FOR NETWORK SHUTDOWN'.format(nodeID))
                        raise KeyboardInterrupt()
                    elif len(command) > 0:
                        # run new command
                        if '{' not in command:
                            # it isn't json args, split by space to get it formatted
                            command = command.split(' ')
                            daemonSubprocesses.append(subprocess.Popen(command))
                        else:
                            # Its in Json, extract out the cmd args at start
                            firstJsonBrack = command.index('{')

                            commandPieces = command[:firstJsonBrack].split(' ')

                            #jsonBody = json.loads(command[firstJsonBrack:])

                            # shell=true originally
                            daemonSubprocesses.append(subprocess.Popen([commandPieces[0], commandPieces[1], command[firstJsonBrack:]]))

                        newProc = daemonSubprocesses[-1]
                        print('Node {}: Daemon Process: New Command {} - {} - {}'.format(nodeID, command, newProc.pid, newProc.returncode))

            # Wait to check again
            time.sleep(batchRate)

    except KeyboardInterrupt:
        pass
    except EOFError as ex1:
        print('EOF Error')
    except Exception as ex:
        print(ex)
    finally:
        Cleanup(daemonSubprocesses, fileInputDir)
