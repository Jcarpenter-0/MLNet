import time
import subprocess
import requests
import json


def runExperiment(NetworkSetupList, Learners, Applications, TestingDuration, ServerCool, KillTimeout, dirOffset='./', keyboardInterupRaise=False):
    """

    :param NetworkSetupList:
    :param Learners:
    :param Applications:
    :param TestingDuration:
    :param ServerCool:
    :param KillTimeout:
    :param dirOffset:
    :param keyboardInterupRaise:
    """
    LearnersProcs = []
    NetworkNodeProcs = []

    keyBoardInterupted = False

    try:

        # Start Network
        for nodeDef in NetworkSetupList:
            NetworkNodeProcs.append(subprocess.Popen(nodeDef))

        print('Network Nodes Setup')

        # Start Learners
        for namePortTrain in Learners:
            learnerDirName = namePortTrain[0]
            learnerCommand = ['python3', '{}learners/{}/run-stub.py'.format(dirOffset, learnerDirName)]
            learnerCommand.extend(namePortTrain[1:])

            LearnersProcs.append(subprocess.Popen(learnerCommand))

        print('Learners Setup')

        # Wait for servers to go up
        time.sleep(ServerCool)

        # Start Applications
        for applicationTargetDef in Applications:
            applicationHost = applicationTargetDef[0]
            applicationArgs = applicationTargetDef[1]
            writeDict = {'args': applicationArgs}

            # convert to json
            jsonBody = json.dumps(writeDict).encode()

            # send to the host server to start the application
            response = requests.post(applicationHost + '/processStart/', data=jsonBody)
            print(response)

        # Wait
        time.sleep(TestingDuration)

    except KeyboardInterrupt as inter:
        keyBoardInterupted = True
    except Exception as ex:
        print(str(ex))
    finally:
        # Stop applications
        for applicationTargetDef in Applications:
            applicationHost = applicationTargetDef[0]

            # send to the host server to start the application
            try:
                response = requests.post(applicationHost + '/processStop/')
                print(response)
            except:
                pass

        # Shutdown/Stop experiment
        for learnerProc in LearnersProcs:
            learnerProc.terminate()
            try:
                learnerProc.wait(KillTimeout)
            except Exception as timeout:
                learnerProc.kill()
                learnerProc.wait()

        # Stop Networks
        for networkNode in NetworkNodeProcs:
            networkNode.terminate()
            try:
                networkNode.wait(KillTimeout)
            except Exception as timeout:
                networkNode.kill()
                networkNode.wait()

        print('Experiment Done')
        if keyboardInterupRaise and keyBoardInterupted:
            raise KeyboardInterrupt


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

            learnerProcs.append(subprocess.Popen(learnerNode.ToArgs()))
            print('Learner: {} - {} - {} online at http://{}:{}/'.format(learnerNode.LearnerTypeName, learnerNode.LearnerLabel, learnerNum, learnerNode.LearnerAddress, learnerNode.LearnerPort))

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
                    print('Application: {} to {}'.format(node.IpAddress, writeDict))
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
