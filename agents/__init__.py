import os
import datetime
import math

# ======================================
# Agent Abstractions
# ======================================


class AgentArgs():

    def __init__(self, agentScriptPath
                 , agentDir='./tmp/'
                 , agentPort=8080
                 , training=1
                 , logPath:str=""
                 , logFileName:str=None
                 , miscArgs:dict=dict()):
        """The collection of arguements to pass to an agent, this is intended as a quick way of formatting args to a agent."""

        self.Agent = agentScriptPath
        self.Args = dict()
        self.Args['-agentDir'] = agentDir
        self.Args['-agentPort'] = agentPort
        self.Args['-training'] = training
        self.Args['-logPath'] = logPath
        self.Args['-logFileName'] = logFileName
        self.Args.update(miscArgs)



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


class DomainModule(object):

    def __init__(self, logPath:str=None, logFileName:str=None, actionFields:dict=None, actionSpace:list=None):
        """The module where domain based edits, translations, and logic occurs.
        If logPath provided, will output data into a csv format.
        If actionFields provided, but no actionSpace, will generate a default naive spanning case.
        If actionSpace is defined, actionFields are ignored.

        """
        # Where to write the logging information to

        self.LogPath:str = logPath
        self.LogFileName: str = logFileName

        self.ExpandObservationFields:bool = True

        if self.LogPath is None or len(self.LogPath) <= 0:
            self.LogPath = None

        if self.LogFileName is None or len(self.LogFileName) <= 0:
            self.LogFileName:str = None

        self.LogFileFullPath: str = ''

        if logPath is not None:
            self.LogFileFullPath:str = self.LogFileFullPath + self.LogPath

        if logFileName is not None:
            self.LogFileFullPath: str = self.LogFileFullPath + self.LogFileName

        if len(self.LogFileFullPath) <= 0:
            self.LogFileFullPath = None

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
            print('{} is {}'.format(key, type(rawObservation[key])))
            if str(type(rawObservation[key])) != '<class \'str\'>':
                print('{} added'.format(rawObservation[key]))
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

        reward = self.DefineReward(rawObservation=rawObservation, observation=observation)

        done = self.DefineDone(rawObservation, observation)

        info = self.DefineInfo(rawObservation)

        if self.LogFileFullPath is not None:
            # Open file for appending
            firstLog = True

            # ensure paths is present
            if self.LogPath is not None:
                try:
                    os.makedirs(self.LogPath, exist_ok=True)
                except Exception as ex:
                    print('Agent: Error making directories. {}'.format(ex))

            if os.path.exists(self.LogFileFullPath):
                firstLog = False

            logFileFP = open(self.LogFileFullPath, 'a')

            if firstLog:
                # Write the header
                expandedHeader = None

                if self.ExpandObservationFields:
                    expandedHeader = ''

                    for metric in rawObservation.keys():
                        expandedHeader += '{},'.format(metric)

                if expandedHeader is None:
                    expandedHeader = 'Raw-Observation'

                logFileFP.write('Timestamp,Reward,Done,Info,{}\n'.format(expandedHeader))

            expandedFields = None

            if self.ExpandObservationFields:
                expandedFields = ''

                for metric in rawObservation.keys():

                    if type(rawObservation[metric]) is str \
                            or type(rawObservation[metric]) is list \
                            or type(rawObservation[metric]) is object\
                            or type(rawObservation[metric]) is dict:
                        expandedFields += '\"{}\",'.format(rawObservation[metric])

                    else:
                        expandedFields += '{},'.format(rawObservation[metric])

            if expandedFields is None:
                expandedFields = '\"{}\"'.format(rawObservation)

            logFileFP.write('{},{},{},\"{}\",{}\n'.format(datetime.datetime.now().strftime("%d-%m-%Y-%H-%M-%S"), reward, done, info, expandedFields))

            logFileFP.flush()
            logFileFP.close()

        return observation, reward, done, info

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

    def __init__(self, repeatActionIndex:int=0):
        """Repeat the same actions as defined, defaulted as the 0th action in the actionspace"""
        super().__init__()
        self.RepeatActionIndex = repeatActionIndex

    def Operate(self, observation, reward, actionSpace, actionSpaceSubset, info) -> int:
       print("Agent-Logic Module: Selecting Action {}".format(self.RepeatActionIndex))
       return self.RepeatActionIndex


# =============================================================
# Common Agent Configs
# =============================================================

def CoreReward(throughputMbps:float, timeCompletionSeconds:float,
               allowedBandwidthMbps:int=None, fairnessWeight:float=0.5) -> (float, float):
    """The basic reward to attempt to distill primary functionality into"""

    tput = throughputMbps
    ttc = timeCompletionSeconds

    if throughputMbps > timeCompletionSeconds:
        digitCount = len(str(int(timeCompletionSeconds))) + 1

        # Divide the larger by the smaller's digit count +1
        tput = throughputMbps/math.pow(10, digitCount)
    elif timeCompletionSeconds > throughputMbps:
        digitCount = len(str(int(throughputMbps)))

        # Divide the larger by the smaller's digit count +1
        ttc = timeCompletionSeconds / math.pow(10, digitCount) + 1

    fairness = 1

    if allowedBandwidthMbps is not None:
        fairness = 1 - (throughputMbps - allowedBandwidthMbps)/allowedBandwidthMbps

    firstTerm = ((1.0 - fairnessWeight) * (tput) * fairness)

    secondTerm = ((fairnessWeight) * (ttc))

    return (firstTerm - secondTerm), fairness
