import time
import datetime
import requests
import json
import shutil
import networks
import apps
import agents.framework_AgentServer


# =======================================
# Registry - What modules are accessible
# =======================================
import networks.mahimahi
import networks.mininet
import networks.netem

networkEnvironments = {}
networkEnvironments['localhost'] = networks.LocalHostNetwork()
networkEnvironments[networks.mahimahi.__name__.split('.')[-1].lower()] = networks.mahimahi.MahiMahiNetwork()
networkEnvironments[networks.mininet.__name__.split('.')[-1].lower()] = networks.mininet.MiniNetNetwork()
networkEnvironments[networks.netem.__name__.split('.')[-1].lower()] = networks.netem.NetemNetwork()

# =======================================
# Framework Abstractions
# =======================================

class Experiment():

    def __init__(self, agents:list, environment:dict):
        """A representation of an "experiment" or the conditions and configurations desired for such.
        This is idealily, directly serializable into an "experiment.json" file. The type of experiment this represents is a simple one, more complex cases must be built using the API calls
        in experiment python scripts. This is intended to be fed into the auto-testing.py system
        """

        self.Repetitions:int = 0
        self.Duration:float = 0.0

        self.Agents:list = agents
        self.Environment = environment



# =======================================
# Framework API Methods
# =======================================


def FindApplicationByArgs(configs:dict, traits:list, network:networks.Network=None, moduleListPath:str='./modules.csv') -> (apps.App, float, list):
    """
    Given a set of paramters, find the best matching application. configs are expected in GAF format. traits just in textual.

    """

    # If a network is already provided, further filter by "node count", and "access"

    return []


def FindNetworkByArgs(configs:dict, traits:list, moduleListPath:str='./modules.csv') -> (list, list, float, list):
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


def SetupExperimentPlan(experiment:dict) -> (dict, list, float, list):
    """Given a set of configs and desired traits, figure out a test plan of modules for environment, and application."""

    # Fill in the missing pieces

    # Find network that matches

    # Find application that matches

    # Return a fully fleshed out test file

    return experiment, [], 0.0, []


def RunExperimentPlanUsingFramework(experimentConfig:dict):
    """Given an experiment plan, execute"""

    exp = Experiment(experimentConfig)

    # Figure out the learner stuff
    learners = []

    for idx, learner in enumerate(exp.agents):

        learnerScriptPath = list(learner.keys())[0]
        learnerArgs = list(learner.values())[0]

        learners.append(agents.framework_AgentServer.AgentWrapper(learnerScriptPath,
                                                                  './tmp/agent-{}/'.format(idx),
                                                                  8080+idx,
                                                                  learnerArgs['training'],
                                                                  logFileName=learnerArgs['log-file-name']))

    # Figure out the environment stuff
    networkModule = None

    # Execute the test
    RunExperimentUsingFramework(networkModule, int(experimentConfig['test-duration-seconds']))


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

