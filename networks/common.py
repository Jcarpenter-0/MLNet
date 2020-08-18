import applications.daemon_server
import subprocess

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

    def AddApplication(self, appArgs):
        self.Applications.append(appArgs)

    def ShutdownNode(self, killTimeout=2):

        self.NodeProc.terminate()
        try:
            self.NodeProc.wait(killTimeout)
        except Exception as timeout:
            self.NodeProc.kill()
            self.NodeProc.wait()


def SetupLocalHost(daemonServerPort=7080, dirOffset='./'):

    # run daemon server
    opServerArgs = applications.daemon_server.PrepareServerArgs(dirOffset=dirOffset, opServerPort=daemonServerPort)

    opProc = subprocess.Popen(opServerArgs,
    stdout=subprocess.PIPE,
    stdin=subprocess.PIPE,
    stderr=subprocess.STDOUT,
    universal_newlines=True)

    return Node(ipAddress='127.0.0.1', daemonPort=daemonServerPort, nodeProc=opProc)