import sys
import time
import datetime
from typing import List
from typing import Dict
import requests
import json
import shutil
import networks
import apps
import agents.framework_AgentServer
import agents as agentsLib
import apps.framework_DMF


# =======================================
# Framework Helper Methods
# =======================================

def ParseExperimentArgs() -> str:

    args = sys.argv[1:]

    # Logging Path
    loggingPath = args[-1]

    return loggingPath




# =======================================
# Framework Abstractions
# =======================================


def EnvironmentArgs() -> dict:
    """The general abstraction of a networking environment"""

    args = dict()

    args.update(apps.framework_DMF.LossDMF().ToDict())
    args.update(apps.framework_DMF.CongestionEventDMF().ToDict())
    args.update(apps.framework_DMF.DataSentDMF().ToDict())
    args.update(apps.framework_DMF.DataReceivedDMF().ToDict())
    args.update(apps.framework_DMF.LatencyDMF().ToDict())
    args.update(apps.framework_DMF.ThroughputDMF().ToDict())
    args.update(apps.framework_DMF.RoundTripTimeDMF().ToDict())

    return args


class Experiment():

    def __init__(self, agents:list, environment:dict):
        """A representation of an "experiment" or the conditions and configurations desired for such.
        This is idealily, directly serializable into an "experiment.json" file. The type of experiment this represents is a simple one, more complex cases must be built using the API calls
        in experiment python scripts. This is intended to be fed into the auto-testing.py system
        """

        self.Repetitions:int = 0
        self.Duration:float = 0.0

        self.Agents:list = agents
        self.Environment:dict = environment

# =======================================
# Framework API Methods
# =======================================


def RunExperimentUsingFramework(network:networks.Network, testDuration:float, appNodeServerCooldown:int=3, interAppDelay:int=1, keyboardInterupRaise:bool=True, shutDownNetworkAfter:bool=True):
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

        if shutDownNetworkAfter:
            network.Shutdown()

        print('Test Complete {}'.format(datetime.datetime.now()))
        if keyboardInterupRaise and keyBoardInterupted:
            raise KeyboardInterrupt

