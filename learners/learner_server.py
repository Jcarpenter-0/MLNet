import http.server
import time
import json
import sys
import signal

# Server code for learners

# Using a "run-stub.py" method in each learner sub directory this will be invoked

# GET will advertise the type of input/output the learner uses

# POST will receive data from applications and then send back responses

Learner = None

def parseArgs():
    # Parse Args
    port = int(sys.argv[1])
    address = ''
    modelMode = int(sys.argv[2])
    modelName = None
    validationPatternFilePath = None
    print('sys args:' + str(sys.argv))
    try:
        modelName = sys.argv[3]
    except:
        pass

    try:
        validationPatternFilePath = sys.argv[4]
    except:
        pass

    try:
        address = sys.argv[5]
    except:
        pass

    return port, address, modelMode, modelName, validationPatternFilePath

def DefineLearner(learner):
    global Learner
    Learner = learner

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

        descriptionDict = Learner.Describe()

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
        returnCommandsDict = Learner.Operate(stateData)

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
        Learner.Conclude()
        self.httpd.shutdown()