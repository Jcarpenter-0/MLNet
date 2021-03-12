import json
import os
import datetime
import mdp

# Helper functions


def DefineSpanningActionSpace(actionFields:dict):
    """List to hold what action para is to be used, will be n entries where n is number of action paras"""
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

    #print('{}'.format(inputPatterns))

    return inputPatterns


# ======================


class Learner(object):

    def __init__(self, learnerScriptPath
                 , learnerDir='./tmp/'
                 , learnerPort=8080
                 , training=1
                 , traceFilePostFix=''
                 , miscArgs=[]):
        """The abstraction of a 'learner' comprised of a ml module, problem definition,
         and a server to host on. Intended to call a learner's setup script in /learners/ and pass some args."""
        self.LearnerScriptPath = learnerScriptPath
        self.LearnerPort = learnerPort

        self.LearnerDir = learnerDir
        self.Training = training

        self.BaseCommand = ['python3', '{}'.format(self.LearnerScriptPath)]

        self.TraceFilePostFix = traceFilePostFix
        self.MiscArgs = miscArgs

    def ToArgs(self):
        """
        :return: a list of cmd line args for use in Popen or cmd
        """
        # return as a python list

        commandArgs = self.BaseCommand.copy()

        commandArgs.extend([
            '{}'.format(self.LearnerPort)
            , ''
            , '{}'.format(self.Training)
            , self.LearnerDir
            , self.TraceFilePostFix])

        commandArgs.extend(self.MiscArgs)

        return commandArgs


class DomainModule(object):

    def __init__(self
                 , loggingDirPath
                 , traceFilePostFix=''
                 , observationFields=[]
                 , actions:dict=dict()
                 , actionSpace:list=None):
        """The Domain translation space.
        Set the translations of state and action and the define the reward.
        Inherit this to define a problem for a learner.
        Observation Fields are just the name of the fields you wish to treat as part of an observation.
        Actions is a dist containing each action parameter (eg: -s) and the range associated with options. Example for Ping
        {'-s':range(56,896,56)}"""

        self.DateFormat = "%d-%m-%Y-%H-%M-%S"

        # Logging and Trace Info
        self.SessionStart = datetime.datetime.now()
        self.CoreDir = loggingDirPath
        self.DomainConfigFilePath = loggingDirPath + 'domainconf.json'
        self.LogFileDir = loggingDirPath + 'Traces/'
        self.LogFilePath = '{}-{}-session-log.csv'.format(self.SessionStart.strftime(self.DateFormat), traceFilePostFix)

        # Ensure the existence of paths
        os.makedirs(self.CoreDir, exist_ok=True)
        os.makedirs(self.LogFileDir, exist_ok=True)

        # Setup the Trace File pointers
        self.LogFileFP = open(self.LogFileDir + self.LogFilePath, 'w')
        self.FirstLogWrite = True

        # define initial total actionSpace
        self.ActionFields = actions
        if actionSpace is None:
            self.ActionSpace = DefineSpanningActionSpace(self.ActionFields)
        else:
            self.ActionSpace = actionSpace

        self.ObservationFields = observationFields

        # Write out the info file
        domainConf = dict()

        domainConf['ActionSpaceSize'] = len(self.ActionSpace)
        domainConf['Actions'] = self.ActionFields
        domainConf['ObservationMetrics'] = self.ObservationFields

        domainConfFP = open(self.DomainConfigFilePath, 'w')

        json.dump(domainConf, domainConfFP, skipkeys=True, indent=8)

        domainConfFP.flush()
        domainConfFP.close()

    def DefineActionSpaceSubset(self):
        """Define the valid range of possible actions as a list of dicts for each valid input pattern."""
        return None

    def DefineReward(self, observation, rawObservation):
        """Define the reward for an observation"""
        return NotImplementedError

    def DefineObservation(self, observation):
        """Define the observations that will make up the state representation"""
        if len(self.ObservationFields) > 0:

            newObv = dict()

            for obvField in self.ObservationFields:
                newObv[obvField] = observation[obvField]

            return newObv
        else:
            return observation

    def RecordObservation(self, observation, reward=None, rawObservation=None):
        """Will simply log the incoming observation to a csv file."""

        obvLog = dict()

        # Add timestamp to the observation
        obvLog['Timestamp'] = datetime.datetime.now().strftime(self.DateFormat)

        # Add reward, if possible
        if reward is not None:
            obvLog['Reward'] = reward

        obvLog.update(observation.copy())

        if rawObservation is not None:
            for rawField in rawObservation:

                obvLog['Raw-{}'.format(rawField)] = "\"{}\"".format(rawObservation[rawField])

        if self.FirstLogWrite:
            # Write out the header
            self.FirstLogWrite = False

            headerLine = ''

            for index, field in enumerate(obvLog.keys()):
                headerLine += '{}'.format(field)

                if index < len(obvLog) - 1:
                    headerLine += ','

            self.LogFileFP.write(headerLine + '\n')

        logLine = ''

        for index, field in enumerate(obvLog.keys()):
            logLine += '{}'.format(obvLog[field])

            if index < len(obvLog) - 1:
                logLine += ','

        self.LogFileFP.write(logLine + '\n')
        self.LogFileFP.flush()

    def Conclude(self):
        """Handles the log closure"""
        print('Learner Concluding')
        # Close the file pointers
        self.LogFileFP.flush()
        self.LogFileFP.close()

    def CallOrder(self, observation):
        """Order to call the methods in when an observation comes in"""

        filteredObservation = self.DefineObservation(observation)

        reward = self.DefineReward(filteredObservation, observation)

        if self.LogFileFP is not None:

            self.RecordObservation(filteredObservation, reward, observation)

        return filteredObservation, reward, observation


class MDPModule(DomainModule):

    def __init__(self, loggingDirPath, mdp:list, traceFilePostFix=''
                 , observationFields=[]
                 , actions:dict=dict()
                 , actionSpace:list=None):

        super().__init__(loggingDirPath=loggingDirPath, traceFilePostFix=traceFilePostFix, observationFields=observationFields, actions=actions, actionSpace=actionSpace)
        self.MDP = mdp
        self.IncomingMetrics = None

    def DefineActionSpaceSubset(self):
        """Action space is defined by what state the system is currently in"""

        # Get current State
        currentState, _ = mdp.AnalyzeObservation(self.IncomingMetrics, self.MDP)

        return currentState.Actions.copy()

    def DefineObservation(self, observation):
        """Observation is provided by the MDP that defines the states"""
        self.IncomingMetrics = observation.copy()

        # Get current State based on metrics
        currentState, id = mdp.AnalyzeObservation(observation, self.MDP)

        # Add to the observation, state id
        newObv = super().DefineObservation(observation)

        newObv['StateID'] = id

        newObv = currentState.AdjustMetrics(newObv)

        return newObv

    def DefineReward(self, observation, rawObservation):
        return NotImplementedError

# Basic ML Modules


class MLModule(object):

    def __init__(self):
        """Essentially a callback class, implement your ML logic and then place the 'step loop' in Operate()"""
        return

    def Operate(self, observation, reward, actionSpace, actionSpaceSubset, info, domainDefinition:DomainModule):
        """Return a dict of action decisions"""
        return NotImplementedError

    def Conclude(self):
        """Called when the learner server goes down"""
        return NotImplemented


class PatternModule(MLModule):

    def __init__(self, pattern:list=None):
        """Simply take send back actions following a pattern regardless of input.
        Pattern expected as an array of dicts. Example [{action1:0, action2:1},{action1:1,action2:0}]"""
        super().__init__()

        self.Pattern = pattern
        self.PatternIndex = 0

    def Operate(self, observation, reward, actionSpace, actionSpaceSubset, info, domainDefinition):

        returnDict = dict()

        if self.Pattern is not None:
            returnDict = self.Pattern[self.PatternIndex]
            self.PatternIndex += 1

            # Handle pattern wrap around
            if self.PatternIndex == len(self.Pattern):
                self.PatternIndex = 0

            print('Learner: Pattern Module - Next Action - {}'.format(returnDict))

        return returnDict

