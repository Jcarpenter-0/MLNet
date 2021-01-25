import apps.daemon_process
import apps.daemon_server
import subprocess
import requests
import time
import json
import os
import shutil


class NetworkModule(object):

    def __init__(self, networkProcs:list=[], nodes:list=[]):
        """A real or simulated network comprised of real or simulated nodes"""

        # Procs for running the network (sim focused, real networks will not likely have this)
        self.NetworkProcs:list = networkProcs

        # List of Node objects (real or simulated)
        self.Nodes:list = nodes

    def StartNodes(self, interNodeDelay=0, interApplicationDelay=0):
        """Start all the nodes's applications"""

        for node in self.Nodes:
            node.StartApplications(interApplicationDelay)
            time.sleep(interNodeDelay)

    def StopNodes(self, interNodeDelay=0, interApplicationDelay=0):
        """Only stop the applications running on the nodes"""
        for node in self.Nodes:
            node.StopApplications()
            time.sleep(interNodeDelay)

    def Shutdown(self, killTimeout=2):
        """Shutdown all the processes on the nodes, and the network itself"""

        # Shutdown each node
        for node in self.Nodes:
            node.ShutdownNode(killTimeout)

        # iterate over network procs to shut them down
        for proc in self.NetworkProcs:
            proc.terminate()
            try:
                proc.wait(killTimeout)
            except Exception as timeout:
                proc.kill()
                proc.wait()
            finally:
                print('Network Shutdown')


class Node(object):

    def __init__(self, ipAddress=None, daemonPort=None, nodeProc=None, inputDir:str=None):
        """

        Applications: List of application Args, list of list
        :param ipAddress: ip address of the node
        :param nodeProc: sub process running this node (used for sim nodes)
        :param daemonPort: Port of daemon server, if none there is no daemon running (and thus use the Proc)
        """
        self.IpAddress = ipAddress
        self.NodeProc = nodeProc
        self.DaemonPort = daemonPort
        self.Applications = []
        self.InputDir:str = inputDir

    def AddApplication(self, appArgs:list):

        appArgsCopy = appArgs.copy()

        for idx, elem in enumerate(appArgs):
            # Ensure string values
            appArgsCopy[idx] = '{}'.format(elem)

        self.Applications.append(appArgsCopy)

    def StartApplications(self, interApplicationDelay=0):
        """Start the applications on the node"""

        for applicationArgs in self.Applications:

            if self.InputDir is not None:
                # no IP or daemon, send data to proc (assuming the file IO based on)
                print('Application: {} to process via file io {}'.format(applicationArgs, self.InputDir))

                cmdLine = ''

                for idx, arg in enumerate(applicationArgs):
                    cmdLine += arg

                    if idx != len(applicationArgs) -1:
                        cmdLine += ' '

                inputFilePath = self.InputDir + 'input.txt'

                inputFP = open(inputFilePath, 'w')

                inputFP.write(cmdLine)

                inputFP.flush()
                inputFP.close()

            elif self.IpAddress is not None and self.DaemonPort is not None:
                # Send "go" via daemon web request

                writeDict = {'args': applicationArgs}

                # convert to json
                jsonBody = json.dumps(writeDict).encode()

                # send to the host server to start the application
                print('Application: {} to http://{}:{}/'.format(writeDict, self.IpAddress, self.DaemonPort))

                response = requests.post('http://{}:{}/processStart/'.format(self.IpAddress, self.DaemonPort),
                                         data=jsonBody)

                if response.ok is False:
                    raise Exception("Problem raising process on node {} : {}".format(self.IpAddress, response.text))

            else:
                raise Exception('Node {} has no daemon'.format(self.IpAddress))

            time.sleep(interApplicationDelay)

    def StopApplications(self):
        """Stop all the applications on a host's daemon.
         Note: for simplicity, any subprocesses being run by the node process must be terminated via other logic than this."""

        try:
            if self.IpAddress is not None and self.DaemonPort is not None:
                # Send "stop" via daemon
                target = 'http://{}:{}/processStop/'.format(self.IpAddress, self.DaemonPort)

                print('Application Stop to {}'.format(target))

                response = requests.post(target)

                if response.ok is False:
                    raise Exception('Could not stop process on node')

            elif self.NodeProc is not None and self.InputDir is not None:

                inputFilePath = self.InputDir + 'input.txt'

                print('Application Stop to {}'.format(inputFilePath))

                cmdLine = 'STOP'

                inputFP = open(inputFilePath, 'w')

                inputFP.write('{}'.format(cmdLine))

                inputFP.flush()
                inputFP.close()

        except Exception as ex:
            print(ex)

    def ShutdownNode(self, killTimeout=2):
        """Completely shutter this node"""
        self.StopApplications()
        print('Shutting down node {}'.format(self.IpAddress))
        if self.NodeProc is not None:

            try:
                self.NodeProc.terminate()
                self.NodeProc.wait(killTimeout)
            except Exception as timeout:
                self.NodeProc.kill()
                self.NodeProc.wait()

            print('{} shutdown'.format(self.IpAddress))
        else:
            print('{} has no proc, but is called to shutdown'.format(self.IpAddress))


def SetupLocalHost(daemonServerPort=7080, dirOffset='./../../', ipAddress:str=None, inputDir:str='./daemon-proc-input/lh/'):

    # run daemon server
    if daemonServerPort is not None:
        opServerArgs = apps.daemon_server.PrepareServerArgs(dirOffset=dirOffset, opServerPort=daemonServerPort)
    else:
        # run daemon proc instead
        try:
            os.makedirs(inputDir)
        except Exception as ex:
            # erase the existing dirs and remake them
            print('Exception making dirs, attempting remake')
            shutil.rmtree(inputDir)
            os.makedirs(inputDir)

        opServerArgs = apps.daemon_process.PrepareDaemonArgs(inputDir, dirOffset=dirOffset)

    opProc = subprocess.Popen(opServerArgs,
    #stdout=subprocess.PIPE,
    stdin=subprocess.PIPE,
    #stderr=subprocess.STDOUT,
    universal_newlines=True)

    print('Localhost node: http://{}:{}/ - {}'.format(ipAddress, daemonServerPort, opProc))

    return Node(ipAddress=ipAddress, daemonPort=daemonServerPort, nodeProc=opProc)