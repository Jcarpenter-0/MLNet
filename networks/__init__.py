import apps.daemon_process
import apps.daemon_server
import subprocess
import requests
import time
import json
import netifaces


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

    def StopNodes(self):
        """Only stop the applications running on the nodes"""
        for node in self.Nodes:
            node.StopApplications()

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



class __networkDefinition(object):

    def __init__(self):
        """Network Definition for the tools registry, intended to have the setup logic
        (cli calls for example) for specific network tools"""
        return

    def Setup(self, setupArgs:dict) -> NetworkModule:
        return NotImplementedError


class Node(object):

    def __init__(self, ipAddress=None, daemonPort=None, nodeProc=None):
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

    def AddApplication(self, appArgs:list):

        appArgsCopy = appArgs.copy()

        for idx, elem in enumerate(appArgs):
            # Ensure string values
            appArgsCopy[idx] = '{}'.format(elem)

        self.Applications.append(appArgsCopy)

    def StartApplications(self, interApplicationDelay=0):
        """Start the applications on the node"""

        for applicationArgs in self.Applications:

            if self.IpAddress is not None and self.DaemonPort is not None:
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

            elif self.NodeProc is not None:
                # no IP or daemon, could use proc, but for my purposes will just error
                print('Application: {} to process'.format(applicationArgs))

                # Add a "background" command to the args
                #applicationArgs.append('&')

                # Add "endline" to signify end of command call
                applicationArgs.append('\n')

                cmdLine = ''

                for arg in applicationArgs:
                    cmdLine += arg + ' '

                self.NodeProc.stdin.write(cmdLine)

                self.NodeProc.stdin.flush()

            else:
                raise Exception('Node {} has no daemon'.format(self.IpAddress))

            time.sleep(interApplicationDelay)

    def StopApplications(self):
        """Stop all the applications on a host's daemon.
         Note: for simplicity, any subprocesses being run by the node process must be terminated via other logic than this."""

        try:
            if self.IpAddress is not None and self.DaemonPort is not None:
                # Send "stop" via daemon
                response = requests.post('http://{}:{}/processStop/'.format(self.IpAddress, self.DaemonPort))

                if response.ok is False:
                    raise Exception('Could not stop process on node')
            else:

                cmdLine = 'STOP'

                self.NodeProc.stdin.write(cmdLine)

                self.NodeProc.stdin.flush()

        except Exception as ex:
            print(ex)

    def ShutdownNode(self, killTimeout=2):
        """Completely shutter this node"""
        self.StopApplications()
        print('Shutting down node {}'.format(self.IpAddress))
        if self.NodeProc is not None:

            self.NodeProc.terminate()
            try:
                self.NodeProc.wait(killTimeout)
            except Exception as timeout:
                self.NodeProc.kill()
                self.NodeProc.wait()

            print('{} shutdown'.format(self.IpAddress))
        else:
            print('{} has no proc, but is called to shutdown'.format(self.IpAddress))


def SetupLocalHost(daemonServerPort=7080, dirOffset='./../../', ipAddress:str=None):

    # run daemon server
    if daemonServerPort is not None:
        opServerArgs = apps.daemon_server.PrepareServerArgs(dirOffset=dirOffset, opServerPort=daemonServerPort)
    else:
        # run daemon proc instead
        opServerArgs = apps.daemon_process.PrepareDaemonArgs(dirOffset=dirOffset)

    opProc = subprocess.Popen(opServerArgs,
    #stdout=subprocess.PIPE,
    stdin=subprocess.PIPE,
    #stderr=subprocess.STDOUT,
    universal_newlines=True)

    print('Localhost node: http://{}:{}/ - {}'.format(ipAddress, daemonServerPort, opProc))

    return Node(ipAddress=ipAddress, daemonPort=daemonServerPort, nodeProc=opProc)