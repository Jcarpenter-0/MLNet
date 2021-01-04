import time
import subprocess
import requests
import json
import pandas as pd
# Contains macros and fast setup abstractions


def runExperimentUsingFramework(networkModule, learnerNodes, testDuration, learnerServerCooldown=6, appNodeServerCooldown=2, killTimeout=3, keyboardInterupRaise=True):
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


def __registerModules() -> dict:
    """Register the modules so that the auto builder may call upon them"""

    modules = dict()



    return modules


def autoBuildEnv(soughtMetrics:list, fit:str='best', networkArgs:dict=None, tags:list=None, envManifestFilePath:str='modules.csv') -> list:
    """Attempt to build an environment for you based on what type of fit
    :return list of Nodes"""

    modules = __registerModules()

    toolsDF = pd.read_csv(envManifestFilePath)

    networkSims = toolsDF[(toolsDF['module'] == 'Host') & (tags in toolsDF['tags']) & (networkArgs in toolsDF['configs'])]

    applications = toolsDF[(toolsDF['module'] == 'Application') & (tags in toolsDF['tags']) & (soughtMetrics in toolsDF['metrics'])]

    if fit is 'best':
        pass
    elif fit is 'absolute':
        pass

    # setup the stuff
    #pingNode = networks.mahimahi.SetupMahiMahiNode([networks.mahimahi.MahiMahiDelayShell(delayMS=MahMahiNetworkDelay)]
    #                                               , dirOffset=DirOffset)

    #pingNode.AddApplication(apps.PrepWrapperCall(PingPath
    #                                                   , InitialPingArgs
    #                                                   , PingRuns
    #                                                  , 'http://100.64.0.1:{}'.format(pingManager.LearnerPort)))


    return []