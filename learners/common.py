import sys
import json
import os
import http.server
import datetime
from typing import Tuple
import signal

# Helper functions

def DefineSpanningActionSpace(actionFields:dict):
    # List to hold what action para is to be used, will be n entries where n is number of action paras
    actionIndices = []

    for actionFieldNum in range(0, len(actionFields)):
        actionIndices.append(0)

    # Get number of possible actions
    numberOfPossibleActions = 1

    for inputField in actionFields.keys():
        inputFieldValues = actionFields[inputField]
        print('Input Field {} - {}'.format(inputField, len(inputFieldValues)))

        numberOfPossibleActions = numberOfPossibleActions * len(inputFieldValues)

    # action para patterns
    inputPatterns = []

    # for all possible patterns of input paras
    for currentActionParaPatternIndex in range(0, numberOfPossibleActions):

        inputPatternDict = dict()

        # for every action and value of actions
        for index, actionField in enumerate(actionFields.keys()):
            actionFieldInputRange = actionFields[actionField]

            inputPlace = actionIndices[index]

            # check for wraparound
            if inputPlace != 0 and inputPlace % len(actionFieldInputRange) == 0:
                actionIndices[index] = 0
                inputPlace = 0

                # increase the previous input's place as well
                if index != 0:
                    actionIndices[index - 1] += 1

            inputPatternDict[actionField] = actionFieldInputRange[inputPlace]

            # increment the action indices
            actionIndices[index] += 1

        inputPatterns.append(inputPatternDict)

    return inputPatterns

# Domain Definition stuff, the session info and the base class of domain


class SessionReport(object):

    def __init__(self):
        """Report for a collected session of metrics"""
        self.SessionDuration = 0


class DomainDefinition(object):

    def __init__(self, loggingDirPath, traceFilePostFix='', observationFields=[], actions:dict=dict()):
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
        self.ReportFilePath = loggingDirPath + 'session-reports.json'
        self.LogFilePath = loggingDirPath + '{}-{}-session-log.csv'.format(self.SessionStart.strftime(self.DateFormat), traceFilePostFix)

        # Ensure the existence of paths
        os.makedirs(self.CoreDir, exist_ok=True)

        # Setup the Trace File pointers
        self.LogFileFP = open(self.LogFilePath, 'w')

        # Write the Trace File header
        self.TraceFields = ['Timestamp', 'Reward']
        self.TraceFields.extend(observationFields)
        self.ObservationFields = observationFields
        self.ActionFields = actions

        headerStr = ''

        for idx, field in enumerate(self.TraceFields):
            headerStr += field
            if idx < len(self.TraceFields):
                headerStr += ','

        self.LogFileFP.write('{}\n'.format(headerStr))
        self.LogFileFP.flush()

        # Session meta info
        self.SessionReport = SessionReport()

    def Describe(self):
        """For human reading"""

        descDict = dict()

        descDict['inputs'] = self.ObservationFields
        #descDict['actions'] = self.ActionFields

        return descDict

    def DefineActionSpace(self):
        """Define the valid range of possible actions as a list of dicts for each valid input pattern."""
        return DefineSpanningActionSpace(self.ActionFields)

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

    def RecordObservation(self, observation, reward=None):
        """Will simply log the incoming observation to a csv file."""

        logLine = ''

        # Add timestamp to the observation
        observation['Timestamp'] = datetime.datetime.now().strftime(self.DateFormat)

        # Add reward, if possible
        if reward is not None:
            observation['Reward'] = reward

        for index, field in enumerate(self.TraceFields):
            logLine += '{}'.format(observation[field])

            if index < len(self.TraceFields):
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

        reward = self.DefineReward(observation)

        if self.LogFilePath is not None:
            self.RecordObservation(observation, reward)

        filteredObservation = self.DefineObservation(observation)

        return filteredObservation, reward, observation

# Basic ML Modules


class MLModule(object):

    def __init__(self):
        """Essentially a callback class, implement your ML logic and then place the 'step loop' in Operate()"""
        return

    def Operate(self, observation, reward, actionSpace, info, domainDefinition:DomainDefinition):
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

    def Operate(self, observation, reward, actionSpace, info, domainDefinition):

        returnDict = self.Pattern[self.PatternIndex]
        self.PatternIndex += 1

        # Handle pattern wrap around
        if self.PatternIndex == len(self.Pattern):
            self.PatternIndex = 0

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

    print('Server args: {} {} {} {} {}'.format(port, learnerAddress, mode, learnerDir, traceFilePostFix))

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

        actionSpace = self.server.DomainDefinition.DefineActionSpace()

        returnCommandsDict = self.server.MLModule.Operate(filteredObv, reward, actionSpace, obv, self.server.DomainDefinition)

        # Convert commands to Json
        returnCommandsJson = json.dumps(returnCommandsDict, indent=5)

        # set HTTP headers
        self.send_response(200)
        self.end_headers()

        # Finish web transaction
        self.wfile.write(returnCommandsJson.encode())


class MLServer(http.server.HTTPServer):

    def __init__(self, domainDefinition: DomainDefinition, mlModule, server_address: Tuple[str, int]):
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
    domainDef = DomainDefinition('', '')

    # Declare a server
    server = MLServer(domainDef, mlModule, ('', 8080))
    print('Server up at http://localhost:{}'.format(8080))
    server.serve_forever()

    print()