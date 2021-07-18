import os
import datetime

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
        self.LogFileName:str = logFileName

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

        reward = self.DefineReward(rawObservation=rawObservation, observation=observation)

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

            if os.path.exists(self.LogPath + self.LogFileName):
                firstLog = False

            logFileFP = open(self.LogPath + self.LogFileName, 'a')

            if firstLog:
                # Write the header
                logFileFP.write('Timestamp,Raw-Observation,Reward,Done,Info\n'.format())

            logFileFP.write('{},\"{}\",{},{},\"{}\"\n'.format(datetime.datetime.now().strftime("%d-%m-%Y-%H-%M-%S"), rawObservation, reward, done, info))

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

    def __init__(self):
        """Repeat the same actions as defined"""
        super().__init__()

    def Operate(self, observation, reward, actionSpace, actionSpaceSubset, info) -> int:
       print("Agent-Logic Module: Selecting Action {}".format(0))
       return 0
