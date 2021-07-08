import os
import datetime
import mdp
import apps

# Helper functions


def DefineSpanningActionSpace(actionFields:dict) -> list:
    """Create a simple span of all possible combinations of a set of action fields.
    Formatted as "actionParaname": range of inputs """
    actionIndices = []

    for actionFieldNum in range(0, len(actionFields)):
        actionIndices.append(0)

    # Get number of possible actions
    numberOfPossibleActions = 1

    for inputField in actionFields.keys():
        inputFieldValues = actionFields[inputField]
        numberOfPossibleActions = numberOfPossibleActions * len(inputFieldValues)

    # action para patterns
    inputPatterns = []

    # for all possible patterns of input paras
    for currentActionParaPatternIndex in range(0, numberOfPossibleActions):

        inputPatternDict = dict()


        # For each input field, and range of inputs for that field
        for index, actionField in enumerate(actionFields.keys()):
            actionFieldInputRange = actionFields[actionField]
            inputPlace = actionIndices[index]

            inputPatternDict[actionField] = actionFieldInputRange[inputPlace]

            # Increment to the next input parameter
            inputPlace += 1

            # check for wraparound, if so reset input place
            if inputPlace >= len(actionFieldInputRange):

                actionIndices[index] = 0
                inputPlace = 0

            actionIndices[index] = inputPlace

        inputPatterns.append(inputPatternDict)

    return inputPatterns


# ======================
# State Adaptive Systems

def CompareDMF(dmf1:apps.DescriptiveMetricFormat, dmf2:apps.DescriptiveMetricFormat) -> (float, list, list):
    """Compare two DMF and produce result match percentage by tags and units, and the intersection of tags and units"""
    return 0.0, [], []

# Conversion Tree is a "thruple" (metric, operation, metric2) in a one-direction, reverse for metric2 to metric1


conversionTree = {
    "bit":{"byte":lambda *x : x[0]/8, "kilobit":lambda *x : x[0]/1000, "bits-per-second": lambda *x: x[0]/x[1]['duration|seconds']},
    "kilobit":{"bit":lambda *x : x[0]*1000, "megabit":lambda *x : x[0]/1000},
    "megabit": {"kilobit":lambda *x : x[0]*1000, "gigabit":lambda *x : x[0]/1000},
    "gigabit":{"megabit":lambda *x : x[0]*1000},
    "byte":{"bit":lambda *x : x[0]*8, "kilobyte":lambda *x : x[0]/1024, "ethernet-packet":lambda *x : x[0]/1500, "ip-packet":lambda *x : x[0]/65535},
    "kilobyte":{"byte":lambda *x : x[0]*1024, "megabyte":lambda *x : x[0]/1024},
    "megabyte":{"kilobyte":lambda *x : x[0]*1024, "gigabyte":lambda *x : x[0]/1024},
    "gigabyte":{"megabyte":lambda *x : x[0]/1024},
    "nanosecond": {"millisecond":lambda *x : x[0]/1000},
    "millisecond":{"nanosecond":lambda *x : x[0]*1000, "second":lambda *x : x[0]/1000},
    "second":{"millisecond":lambda *x : x[0]*1000, "minute":lambda *x : x[0]/60},
    "minute":{"second":lambda *x : x[0]*60, "hour":lambda *x : x[0]/60},
    "hour":{"minute":lambda *x : x[0]*60, "day":lambda *x : x[0]/24},
    "day":{"hour":lambda *x : x[0]*24, "year":lambda *x : x[0]/365},
    "year":{"day":lambda *x : x[0]*365, "decade":lambda *x : x[0]/10},
    "decade":{"year":lambda *x : x[0]*24, "century":lambda *x : x[0]/10},
    "century":{"decade":lambda *x : x[0]*10},
    "ethernet-packet":{"byte":lambda *x : x[0]*1500},
    "ip-packet":{"byte":lambda *x : x[0]*65535},
    "bits-per-second":{"bit": lambda *x : x[0] * x[1]["duration|seconds"], "kilobits-per-second":lambda *x : x[0]/1000},
    "kilobits-per-second": {"bits-per-second":lambda *x : x[0]*1000, "kilobits-per-second":lambda *x : x[0]/1000},
    "megabits-per-second":{"kilobits-per-second":lambda *x : x[0]*1000, "gigabits-per-second":lambda *x : x[0]/1000},
    "gigabits-per-second":{"megabits-per-second":lambda *x : x[0]*1000}
}


def __getMetric(desiredMetric:apps.DescriptiveMetricFormat, observation:dict, conversionTree:dict=conversionTree) -> apps.DescriptiveMetricFormat:
    """Find a metric (or convert a metric) in an observation.
    Will construct the connectives from the metric, then try to find the closest metric from the observation
    """

    # Convert observation to DMF list
    dmfMetrics = []

    for key in observation:
        newDMF = apps.ParseDMF(key, observation[key])

        dmfMetrics.append(newDMF)

    return None


def __createConversionBFSTree(rootMetric:str, conversionTree:dict=conversionTree) -> dict:
    """Build a bfs tree"""
    # new tree
    newTree = {}

    # seen
    seen = []

    # the bfs list
    processNext = {rootMetric:conversionTree[rootMetric]}

    while len(processNext.keys()) > 0:
        # process next node
        currentNodeName = list(processNext.keys())[0]

        seen.append(currentNodeName)

        currentNode = processNext.pop(currentNodeName)

        currentNodeConnections = list(currentNode.keys())

        # Add new branches
        for key in currentNodeConnections:
            if key not in seen:
                newTree[key] = currentNodeName
                processNext[key] = conversionTree[key]

    return newTree


def __resolveMetricPath(startMetric:str, endMetric:str, conversionTree:dict=conversionTree) -> list:
    """Using Breadth-First Search, traverse a conversionTree, create a new tree for operation resolution."""

    newTree = __createConversionBFSTree(endMetric, conversionTree)

    # return the path
    path = []

    if startMetric in newTree.keys():

        nextNode = startMetric

        while nextNode is not None:
            path.append(nextNode)

            if nextNode is not endMetric:
                nextNode = newTree[nextNode]
            else:
                nextNode = None

    return path


def AdjustMetric(startDMFValue:float, startDMF:str, endDMF:str, conversionTree:dict=conversionTree) -> (float, list):
    """From a starting point to an ending point, do the operations in the conversion tree until end reached.
    Return warnings and the adjusted value (up to the point it can't go without more adjustment)"""

    warnings = []
    onGoingMetric = startDMFValue

    startMetricTags = set(startDMF.split('|'))

    endMetricTags = set(endDMF.split('|'))

    resolveTags = startMetricTags - endMetricTags

    if len(resolveTags) > 0:
        warnings.append("There are {} tags to convert/adjust".format(len(resolveTags)))

    for tag in resolveTags:

        # "eliminate" the metrics that exist in start but not end
        if tag in startMetricTags and tag not in endMetricTags:
            onGoingMetric = conversionTree[0][tag]

        # "add" the metrics that exist in end but not start
        if tag not in startMetricTags and tag in endMetricTags:
            onGoingMetric = conversionTree[0][tag]

    return (onGoingMetric, warnings)

# ==========================


class DomainModule(object):

    def __init__(self, logPath:str=None, actionFields:dict=None, actionSpace:list=None):
        """The module where domain based edits, translations, and logic occurs.
        If logPath provided, will output data into a csv format.
        If actionFields provided, but no actionSpace, will generate a default naive spanning case.
        If actionSpace is defined, actionFields are ignored.

        """
        # Where to write the logging information to
        self.LogPath:str = logPath

        if actionFields is not None:
            # Define default actions case
            self.ActionSpace:list = DefineSpanningActionSpace(actionFields)
        else:
            self.ActionSpace:list = actionSpace

    def DefineActionspace(self, rawObservation:dict, observation:list) -> list:
        """Define the entire list of possible actions that a learner may select from."""
        if self.ActionSpace is None:
            return NotImplementedError
        else:
            return self.ActionSpace

    def DefineActionspaceSubset(self, rawObservation:dict, observation:list) -> list:
        """Return the indices of the "available" actions. By default, will return no subset."""
        return None

    def DefineReward(self, rawObservation:dict, observation:list) -> float:
        """Define the reward based on information from the observations"""
        return NotImplementedError

    def DefineObservation(self, rawObservation:dict) -> list:
        """Filter, adjust, and convert raw observations into 'cleaner' observation representation.
        By default, will just flatten the observation dict then drop non-numeric fields."""

        observation = []

        for key in rawObservation.keys():
            if type(rawObservation[key]) != 'str':
                observation.append(rawObservation[key])

        return observation

    def DefineDone(self, rawObservation:dict, observation:list) -> bool:
        """Determine if the agent's work is 'done', this is included for completness,
         but logically difficult in live systems. By default, returns False eg: not done."""
        return False

    def DefineInfo(self, rawObservation:dict) -> dict:
        """Raw information, agent state, and other misc information"""
        return {"domain-module": self, "raw-observation":rawObservation}

    def Process(self, rawObservation:dict) -> (list, float, bool, dict):
        """Process incoming observations, return full OpenAIGym formatted RL data: observation, reward, done, and info.
        Also, provide logging of this information to a specificed logPath in csv format."""

        observation = self.DefineObservation(rawObservation)

        reward = self.DefineReward(rawObservation, observation)

        done = self.DefineDone(rawObservation, observation)

        info = self.DefineInfo(rawObservation)

        if self.LogPath is not None:
            # Open file for appending
            firstLog = True

            # ensure paths is present
            try:
                os.makedirs(self.LogPath, exist_ok=True)
            except Exception as ex:
                print('Agent: Error making directories. {}'.format(ex))

            if os.path.exists(self.LogPath):
                firstLog = False

            logFileFP = open(self.LogPath, 'a')

            if firstLog:
                # Write the header
                logFileFP.write('Raw-Observation,Reward,Done,Info\n'.format())

            logFileFP.write('{},{},{},{},{}\n'.format(datetime.datetime.now().strftime("%d-%m-%Y-%H-%M-%S"), rawObservation.__dict__, reward, done, info.__dict__))

            logFileFP.flush()
            logFileFP.close()

        return observation, reward, done, info


class PartialMDPModule(DomainModule):

    def __init__(self, mdp:list, logPath:str=None, actionSpace:list=None, actionFields:dict=None):
        """Partial-defined Markovian Decision Process system"""
        super().__init__(logPath=logPath, actionSpace=actionSpace, actionFields=actionFields)
        self.MDP = mdp

    def DefineActionSpaceSubset(self, rawObservation:dict, observation:dict) -> list:
        """Action space is defined by what state the system is currently in"""

        # Get current State
        currentState, _ = mdp.AnalyzeObservation(rawObservation, self.MDP)

        return currentState.Actions.copy()

    def DefineObservation(self, rawObservation:dict) -> list:
        """Observation is provided by the MDP that defines the states"""

        # Get current State based on metrics
        currentState, id = mdp.AnalyzeObservation(rawObservation, self.MDP)

        rawObservation['StateID'] = id

        # Add to the observation, state id
        newObv = super().DefineObservation(rawObservation)

        newObv = currentState.AdjustMetrics(newObv)

        return newObv


class AdaptationModule(DomainModule):

    def __init__(self):
        """Domain Module that will, given a desired set of observation metrics, attempt to ensure that any data coming in conforms that standard."""
        super().__init__()

    def DefineObservation(self, rawObservation:dict) -> list:
        """Use basic adaptation to ensure consistency of metrics"""

        return super().DefineObservation(rawObservation)

# Basic Logic Modules


class LogicModule(object):

    def __init__(self):
        """Essentially a callback class, implement your ML logic and then place the 'step loop' in Operate()"""

    def Operate(self, observation, reward, actionSpace, actionSpaceSubset, info) -> int:
        """Return index of selected action from actionspace"""
        return NotImplementedError

    def Conclude(self):
        """Called when the learner must "finish" or close."""
        return NotImplemented


class RepeatModule(LogicModule):

    def __init__(self):
        """Repeat the same actions as defined"""
        super().__init__()

    def Operate(self, observation, reward, actionSpace, actionSpaceSubset, info) -> int:
       print("Agent-Logic Module: Selecting Action {}".format(0))
       return 0
