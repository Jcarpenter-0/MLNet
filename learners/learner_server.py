import http.server
import time
import json
import sys
import signal

# Server code for learners

# Using a "run-stub.py" method in each learner sub directory this will be invoked

# GET will advertise the type of input/output the learner uses

# POST will receive data from applications and then send back responses

_serverLearnerModule = None


def parseArgs(verbose=False):
    '''
        Just parses the common args passed to the server: port, address, mode, name, etc
    '''

    # Parse Args
    if verbose:
        print('sys args:' + str(sys.argv))
    port = int(sys.argv[1])
    address = ''
    try:
        address = sys.argv[2]
    except:
        pass
    learnerMode = int(sys.argv[3])
    learnerName = sys.argv[4]
    traceFilePrefix = ''
    try:
        traceFilePrefix = sys.argv[5]
    except:
        pass
    validationPatternFilePath = None
    try:
        validationPatternFilePath = sys.argv[6]
    except:
        pass

    return port, address, learnerMode, learnerName, validationPatternFilePath, traceFilePrefix


class LearnerNode(object):

    def __init__(self,
                 learnerTypeName
                 , learnerPort=8080
                 , learnerAddress=None
                 , learnerMode=1
                 , learnerLabel=None
                 , traceLabel=None
                 , validationPatternFilePath=None
                 , dirOffset='./'):
        """

        """
        self.LearnerTypeName = learnerTypeName
        self.LearnerPort = learnerPort
        self.LearnerAddress = learnerAddress
        if self.LearnerAddress is None:
            self.LearnerAddress = ''

        self.LearnerMode = learnerMode
        self.LearnerLabel = learnerLabel
        if self.LearnerLabel is None:
            self.LearnerLabel = ''

        self.TraceLabel = traceLabel
        if self.TraceLabel is None:
            self.TraceLabel = ''

        self.ValidationPatternFilePath = validationPatternFilePath
        if validationPatternFilePath is None:
            self.ValidationPatternFilePath = ''

        self.BaseCommand = ['python3', '{}learners/{}/run-stub.py'.format(dirOffset, learnerTypeName)]

    def ToArgs(self, shell=False):
        """
        :return: a list of cmd line args for use in Popen or cmd
        """

        if shell:
            # return as a string
            return '{} {} {} {} {} {} {} {}'.format(
                self.BaseCommand[0]
                , self.BaseCommand[1]
                , self.LearnerPort
                , self.LearnerAddress
                , self.LearnerMode
                , self.LearnerLabel
                , self.TraceLabel
                , self.ValidationPatternFilePath)
        else:
            # return as a python list

            commandArgs = self.BaseCommand.copy()

            commandArgs.extend([
                 '{}'.format(self.LearnerPort)
                , self.LearnerAddress
                , '{}'.format(self.LearnerMode)
                , self.LearnerLabel
                , self.TraceLabel
                , self.ValidationPatternFilePath])

            return commandArgs


# Hack to force server to use server properly
def DefineLearner(learner):
    global _serverLearnerModule
    _serverLearnerModule = learner


class OperationServerHandler(http.server.SimpleHTTPRequestHandler):

    def do_GET(self):

        requestTimeStart = time.time()

        # based on asset type, change cc
        print(self.path)

        # load in the asset
        itemPath = self.path

        # browser agent
        browser = self.headers['User-Agent']

        # http version
        httpVersion = self.protocol_version

        descriptionDict = _serverLearnerModule.Describe()

        jsonDescription = json.dumps(descriptionDict, indent=5)

        # set the headers
        self.send_response(200)
        self.end_headers()

        self.wfile.write(jsonDescription.encode())

        requestTimeEnd = time.time()

        requestCompletionTime = requestTimeEnd - requestTimeStart

    def do_POST(self):

        # Parse out necessary parameters
        length = int(self.headers['content-length'])
        postDataRaw = self.rfile.read(length)

        # Convert from POST to dict
        stateData = json.loads(postDataRaw)

        # Call Learner's Operate, this will do the Observation -> Act (or Train and Act) or Train only or act only
        returnCommandsDict = _serverLearnerModule.Operate(stateData)

        # Convert commands to Json
        returnCommandsJson = json.dumps(returnCommandsDict, indent=5)

        # set HTTP headers
        self.send_response(200)
        self.end_headers()

        # Finish web transaction
        self.wfile.write(returnCommandsJson.encode())


class OperationServer(object):
    def __init__(self, serverAddress, port):
        self.serverAddress = (serverAddress, port)
        self.httpd = http.server.HTTPServer(self.serverAddress, OperationServerHandler)
        self.Operate = True
        signal.signal(signal.SIGTERM, self.cleanup)

    def run(self):
        while self.Operate:
            self.httpd.handle_request()

    def cleanup(self):
        print('Learner Server Cleaning up')
        self.Operate = False
        _serverLearnerModule.Conclude()
        self.httpd.shutdown()