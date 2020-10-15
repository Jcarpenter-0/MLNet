import time
import subprocess
import requests
import json
# Contains macros and fast setup abstractions

# Fast setup abstractions


class Learner(object):

    def __init__(self, learnerScriptPath
                 , learnerDir='./tmp/'
                 , learnerPort=8080
                 , learnerAddress=None
                 , training=1
                 , traceFilePostFix=''
                 , miscArgs=[]):
        """The abstraction of a 'learner' comprised of a ml module, problem definition,
         and a server to host on. Intended to call a learner's setup script in /learners/ and pass some args."""
        self.LearnerScriptPath = learnerScriptPath
        self.LearnerPort = learnerPort
        self.LearnerAddress = learnerAddress
        if self.LearnerAddress is None:
            self.LearnerAddress = ''

        self.LearnerDir = learnerDir
        self.Training = training

        self.BaseCommand = ['python3', '{}'.format(self.LearnerScriptPath)]

        self.TraceFilePostFix = traceFilePostFix
        self.MiscArgs = miscArgs

    def ToArgs(self, shell=False):
        """
        :return: a list of cmd line args for use in Popen or cmd
        """

        if shell:
            # return as a string
            return '{} {} {} {} {}'.format(
                self.BaseCommand[0]
                , self.BaseCommand[1]
                , self.LearnerPort
                , self.LearnerAddress
                , self.Training
                , self.LearnerDir)
        else:
            # return as a python list

            commandArgs = self.BaseCommand.copy()

            commandArgs.extend([
                '{}'.format(self.LearnerPort)
                , self.LearnerAddress
                , '{}'.format(self.Training)
                , self.LearnerDir
                , self.TraceFilePostFix])

            commandArgs.extend(self.MiscArgs)

            return commandArgs


def runExperimentUsingFramework(networkNodes, learnerNodes, testDuration, serverCooldown=5, killTimeout=3, keyboardInterupRaise=True, shutDownNetworkWhenDone=True):
    """
        Outline assumptions here:
        -Daemon server on hosts
        -Network already setup with nodes setup (running daemon servers)
        -Learners all on same original host

    :param networkNodes:
    :param learnerNodes:
    :param testDuration:
    :param serverCooldown:
    :param killTimeout:
    :param keyboardInterupRaise:
    """
    learnerProcs = []

    keyBoardInterupted = False

    try:

        # Start Learners
        for learnerNum, learnerNode in enumerate(learnerNodes):

            # Adjust the ports so there is no overlap
            learnerNode.LearnerPort = learnerNode.LearnerPort + learnerNum

            newProc = subprocess.Popen(learnerNode.ToArgs())

            learnerProcs.append(newProc)
            print('Learner: {} - {} - {} {} at http://{}:{}/'.format(learnerNode.LearnerScriptPath, learnerNode.LearnerDir, learnerNum, newProc.returncode, learnerNode.LearnerAddress, learnerNode.LearnerPort))

        # Wait for servers to go up
        time.sleep(serverCooldown)

        # Start Applications on the nodes, first run the daemon server, then send the commands
        for nodeNum, node in enumerate(networkNodes):

            for applicationArgs in node.Applications:

                if node.IpAddress is not None and node.DaemonPort is not None:
                    # Send "go" via daemon web request

                    writeDict = {'args': applicationArgs}

                    # convert to json
                    jsonBody = json.dumps(writeDict).encode()

                    # send to the host server to start the application
                    print('Application: {} to http://{}:{}/'.format(writeDict, node.IpAddress, node.DaemonPort))

                    response = requests.post('http://{}:{}/processStart/'.format(node.IpAddress, node.DaemonPort), data=jsonBody)
                    if response.ok is False:
                        raise Exception("Problem raising process on node {} : {}".format(node.IpAddress, response.text))

                else:
                    # no IP or daemon, could use proc, but for my purposes will just error
                    raise Exception('Node {} has no daemon'.format(nodeNum))

        # Wait for whole test
        time.sleep(testDuration)

    except KeyboardInterrupt as inter:
        keyBoardInterupted = True
    except Exception as ex:
        print(str(ex))
    finally:
        # Stop applications
        for nodeNum, node in enumerate(networkNodes):

            try:
                if node.IpAddress is not None and node.DaemonPort is not None:
                    # Send "stop" via daemon
                    response = requests.post('http://{}:{}/processStop/'.format(node.IpAddress, node.DaemonPort))

                    if response.ok is False:
                        raise Exception('Could not stop process on node')
            except Exception as ex:
                print(ex)
            finally:
                # stop network node
                if shutDownNetworkWhenDone:
                    node.ShutdownNode()
                    print('Node {} shutdown'.format(node.IpAddress))

        # Shutdown/Stop experiment
        for learnerProc in learnerProcs:
            learnerProc.terminate()
            try:
                learnerProc.wait(killTimeout)
            except Exception as timeout:
                learnerProc.kill()
                learnerProc.wait()

        print('Experiment Done')
        if keyboardInterupRaise and keyBoardInterupted:
            raise KeyboardInterrupt
