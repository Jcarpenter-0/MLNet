import sys
import json
import os
import http.server
import datetime
from typing import Tuple
import signal
import time
import mdp


class Learner(object):

    def __init__(self, learnerScriptPath
                 , learnerDir='./tmp/'
                 , learnerPort=8080
                 , learnerAddress=None
                 , training=1
                 , traceFilePostFix=''
                 , miscArgs=[]):
        """The abstraction of a 'learner' comprised of a ml module, problem definition,
         and a server to host on. Intended to call a learner's setup script in /learners/ and pass some args."""
        self.LearnerScriptPath = learnerScriptPath
        self.LearnerPort = learnerPort
        self.LearnerAddress = learnerAddress
        if self.LearnerAddress is None:
            self.LearnerAddress = ''

        self.LearnerDir = learnerDir
        self.Training = training

        self.BaseCommand = ['python3', '{}'.format(self.LearnerScriptPath)]

        self.TraceFilePostFix = traceFilePostFix
        self.MiscArgs = miscArgs

    def GetURL(self) -> str:
        return 'http://{}:{}/'.format(self.LearnerAddress, self.LearnerPort)

    def ToArgs(self, shell=False):
        """
        :return: a list of cmd line args for use in Popen or cmd
        """

        if shell:
            # return as a string
            return '{} {} {} {} {}'.format(
                self.BaseCommand[0]
                , self.BaseCommand[1]
                , self.LearnerPort
                , self.LearnerAddress
                , self.Training
                , self.LearnerDir)
        else:
            # return as a python list

            commandArgs = self.BaseCommand.copy()

            commandArgs.extend([
                '{}'.format(self.LearnerPort)
                , self.LearnerAddress
                , '{}'.format(self.Training)
                , self.LearnerDir
                , self.TraceFilePostFix])

            commandArgs.extend(self.MiscArgs)

            return commandArgs


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

# Domain Definition stuff, the session info and the base class of domain


class SessionReport(object):

    def __init__(self):
        """Report for a collected session of metrics"""
        self.SessionDuration = 0


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
        self.ReportFilePath = loggingDirPath + 'session-reports.json'
        self.LogFileDir = loggingDirPath + 'Traces/'
        self.LogFileName = '{}-{}-session-log.csv'.format(self.SessionStart.strftime(self.DateFormat), traceFilePostFix)

        # Ensure the existence of paths
        os.makedirs(self.CoreDir, exist_ok=True)
        os.makedirs(self.LogFileDir, exist_ok=True)

        # Setup the Trace File pointers
        self.LogFileFP = open(self.LogFileDir + self.LogFileName, 'w')
        self.FirstLogWrite = True

        # define initial total actionSpace
        self.ActionFields = actions
        if actionSpace is None:
            self.ActionSpace = DefineSpanningActionSpace(self.ActionFields)
        else:
            self.ActionSpace = actionSpace

        self.ObservationFields = observationFields

        # Session meta info
        #self.SessionReport = SessionReport()

        # Write out the info file
        domainConf = dict()

        domainConf['ActionSpaceSize'] = len(self.ActionSpace)
        domainConf['Actions'] = self.ActionFields
        domainConf['ObservationMetrics'] = self.ObservationFields

        domainConfFP = open(self.DomainConfigFilePath, 'w')

        json.dump(domainConf, domainConfFP, skipkeys=True, indent=8)

        domainConfFP.flush()
        domainConfFP.close()

    def Describe(self):
        """For human reading"""

        descDict = dict()

        descDict['inputs'] = self.ObservationFields
        #descDict['actions'] = self.ActionFields

        return descDict

    def DefineActionSpaceSubset(self):
        """Define the valid range of possible actions as a list of dicts for each valid input pattern."""
        return None

    def DefineReward(self, observation):
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

        # Close the file pointers
        self.LogFileFP.flush()
        self.LogFileFP.close()

        # Open the report, append info to it

        # Close the report

    def CallOrder(self, observation):
        """Order to call the methods in when an observation comes in"""

        filteredObservation = self.DefineObservation(observation)

        reward = self.DefineReward(filteredObservation)

        if self.LogFileFP is not None:

            self.RecordObservation(filteredObservation, reward, observation)

        return filteredObservation, reward, observation


class MDPModule(DomainModule):

    def __init__(self, loggingDirPath, mdp:list):
        super().__init__(loggingDirPath)
        self.MDP = mdp
        self.IncomingMetrics = None

    def DefineActionSpaceSubset(self):
        """Action space is defined by what state the system is currently in"""

        # Get current State
        currentState, _ = mdp.AnalyzeObservation(self.IncomingMetrics, self.MDP)

        return currentState.Actions.copy()

    def DefineObservation(self, observation):
        """Observation is provided by the MDP that defines the states"""
        self.IncomingMetrics = observation.copy

        # Get current State based on metrics
        currentState, id = mdp.AnalyzeObservation(observation, self.MDP)

        # Add to the observation, state id
        newObv = observation.copy

        newObv['StateID'] = id

        newObv = currentState.AdjustMetrics(newObv)

        return newObv

    def DefineReward(self, observation):
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

        returnDict = self.Pattern[self.PatternIndex]
        self.PatternIndex += 1

        # Handle pattern wrap around
        if self.PatternIndex == len(self.Pattern):
            self.PatternIndex = 0

        print('Pattern Module - Next Action - {}'.format(returnDict))

        return returnDict

# SERVER STUFF


def ParseDefaultServerArgs():

    port = int(sys.argv[1])
    learnerAddress = sys.argv[2]
    mode = int(sys.argv[3])
    learnerDir = sys.argv[4]
    traceFilePostFix = sys.argv[5]
    miscArgs = None
    if len(sys.argv) >= 6:
        miscArgs = sys.argv[6:]

    print('Server args: {} {} {} {} {} {}'.format(port, learnerAddress, mode, learnerDir, traceFilePostFix, miscArgs))

    return port, learnerAddress, mode, learnerDir, traceFilePostFix, miscArgs


class MLHttpHandler(http.server.SimpleHTTPRequestHandler):

    def do_GET(self):
        """Provides the domain definition of what the learner is trying to solve"""
        descriptionDict = self.server.DomainDefinition.Describe()

        jsonDescription = json.dumps(descriptionDict, indent=5, skipkeys=True)

        # set the headers
        self.send_response(200)
        self.end_headers()

        self.wfile.write(jsonDescription.encode())

    def do_POST(self):
        """Receives observations from the environment, then responds with the next action that should be taken"""
        # Parse out necessary parameters
        length = int(self.headers['content-length'])
        postDataRaw = self.rfile.read(length)

        # Convert from POST to dict
        observation = json.loads(postDataRaw)

        # Process the info through the domain definition
        filteredObv, reward, obv = self.server.DomainDefinition.CallOrder(observation)

        actionSpaceSubset = self.server.DomainDefinition.DefineActionSpaceSubset()

        returnCommandsDict = self.server.MLModule.Operate(filteredObv, reward, self.server.DomainDefinition.ActionSpace, actionSpaceSubset, obv, self.server.DomainDefinition)

        # Convert commands to Json
        returnCommandsJson = json.dumps(returnCommandsDict, indent=5)

        # set HTTP headers
        self.send_response(200)
        self.end_headers()

        # Finish web transaction
        self.wfile.write(returnCommandsJson.encode())


class MLServer(http.server.HTTPServer):

    def __init__(self, domainDefinition: DomainModule, mlModule, server_address: Tuple[str, int]):
        """ML HTTP Server, will stand as endpoint to receive observations
        from environment and send out actions as response to requests."""
        super().__init__(server_address, MLHttpHandler)

        # Indicate that sigterm should call shutdown of the server
        signal.signal(signal.SIGTERM, self.Cleanup)

        self.DomainDefinition = domainDefinition
        self.MLModule = mlModule

    def Cleanup(self):

        # Shutdown the server
        self.shutdown()

        # Handle the domain def's conclusion
        self.DomainDefinition.Conclude()

        # Handle the module's conclusions
        self.MLModule.Conclude()


if __name__ == '__main__':

    # Example of a run-stub that will be called by an experiment script

    # Declare a learner(here a pattern)
    mlModule = PatternModule(pattern=[{'act':1 ,'act2':0}])

    # Define the domain knowledge
    domainDef = DomainModule('', '')

    # Declare a server
    server = MLServer(domainDef, mlModule, ('', 8080))
    print('Learner: http://localhost:{}'.format(8080))
    try:
        server.serve_forever()
    except Exception as ex:
        print(ex)
        errorFP = open('learner-error-{}.txt'.format(time.time()), 'w')

        errorFP.write('{}'.format(ex))

        errorFP.flush()
        errorFP.close()
