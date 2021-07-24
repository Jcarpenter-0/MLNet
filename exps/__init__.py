import time
import datetime
import requests
import json
import shutil
import networks
import apps

# =======================================
# Registry - What modules are accessible
# =======================================

# =======================================
# Framework API Methods
# =======================================


def SetupApplicationByArgs(configs:dict) -> (apps.App, float, list):
    """
    Given a set of paramters, find the best matching application

    :param configs:
    :return:
    """

    return []


def SetupNetworkByArgs(configs:dict) -> (networks.Network, list, float, list):
    """
    Given a set of desired configs, find the closest matching network system and set it up.

    :param configs:
    :return: network, list of unresolved traits, match degree, list of warnings
    """

    network = None
    unresolved = []
    warnings = []
    matchDegree = 0.0

    # Load in the "library of modules"

    # Do basic match

    # return highest match

    return (network, unresolved, matchDegree, warnings)


def RunExperimentUsingFramework(network:networks.Network, testDuration:int, appNodeServerCooldown:int=3, interAppDelay:int=2, keyboardInterupRaise:bool=True):
    """
        Outline assumptions here:
        -Daemon server on hosts
        -Network already setup with nodes setup (running daemon servers)

    :param network:
    :param testDuration:
    :param killTimeout:
    :param keyboardInterupRaise:
    """

    keyBoardInterupted = False

    # calculate number of apps
    appCount = 0

    for node in network.Nodes:
        appCount += len(node.Applications)

    # calulate meta info
    testDurationInSeconds = testDuration + (len(network.Nodes) * appNodeServerCooldown) + (appCount * interAppDelay)

    print('Test: ~{} hour(s) = ~{} second(s)'.format(testDurationInSeconds/60/60, testDurationInSeconds))

    try:
        setupStart = datetime.datetime.now()
        print('Test: Setup started: {}'.format(setupStart))
        time.sleep(appNodeServerCooldown)

        network.StartNodes(interNodeDelay=appNodeServerCooldown, interApplicationDelay=interAppDelay)

        testBegin = datetime.datetime.now()
        print('Test: Setup complete: {} | Setup delay(ms) {}'.format(testBegin, (testBegin - setupStart).microseconds * 1000))

        # Wait for whole test
        time.sleep(testDuration)

    except KeyboardInterrupt as inter:
        keyBoardInterupted = True
    except Exception as ex:
        print(str(ex))
    finally:
        # Stop Applications on the nodes
        network.StopNodes(interNodeDelay=appNodeServerCooldown)

        print('Test Complete {}'.format(datetime.datetime.now()))
        if keyboardInterupRaise and keyBoardInterupted:
            raise KeyboardInterrupt

