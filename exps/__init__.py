import time
import subprocess


def runExperimentUsingFramework(networkModule, learnerNodes:list, testDuration:int, learnerServerCooldown:int=6, appNodeServerCooldown:int=2, killTimeout:int=3, keyboardInterupRaise:bool=True):
    """
        Outline assumptions here:
        -Daemon server on hosts
        -Network already setup with nodes setup (running daemon servers)
        -Learners all on same original host

    :param networkModule:
    :param learnerNodes:
    :param testDuration:
    :param learnerServerCooldown:
    :param killTimeout:
    :param keyboardInterupRaise:
    """
    learnerProcs = []

    keyBoardInterupted = False

    # calulate meta info
    testDurationInSeconds = testDuration + learnerServerCooldown + (len(networkModule.Nodes) * appNodeServerCooldown)

    print('Experimental Run: ~{} hour(s)'.format(testDurationInSeconds/60/60))

    try:

        # Start Learners
        for learnerNum, learnerNode in enumerate(learnerNodes):

            newProc = subprocess.Popen(learnerNode.ToArgs())

            learnerProcs.append(newProc)
            print('Learner: {} - {} - {} {} at http://{}:{}/'.format(learnerNode.LearnerScriptPath, learnerNode.LearnerDir, learnerNum, newProc.returncode, learnerNode.LearnerAddress, learnerNode.LearnerPort))

        # Wait for servers to go up
        time.sleep(learnerServerCooldown)

        networkModule.StartNodes(interNodeDelay=appNodeServerCooldown)

        # Wait for whole test
        time.sleep(testDuration)

    except KeyboardInterrupt as inter:
        keyBoardInterupted = True
    except Exception as ex:
        print(str(ex))
    finally:
        # Stop apps
        print('Stopping Apps')
        networkModule.StopNodes()

        # Shutdown/Stop experiment
        print('Stopping Learner(s)')
        for learnerProc in learnerProcs:

            try:
                learnerProc.terminate()
                learnerProc.wait(killTimeout)
            except Exception as timeout:
                learnerProc.kill()
                learnerProc.wait()

        print('Experiment Done')
        if keyboardInterupRaise and keyBoardInterupted:
            raise KeyboardInterrupt
