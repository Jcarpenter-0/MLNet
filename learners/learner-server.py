import http.server
import sys
import time
import json


# Server code for learners

# GET will advertise the type of input/output the learner uses

# POST will recieve data from applications and then send back responses

# This code will plug in a model

# Harness for running Applications

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

        self.wfile.write(jsonDescription.encode())

        self.send_response(200)
        self.end_headers()

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

        # Finish web transaction
        self.wfile.write(returnCommandsJson.encode())

        self.send_response(200)
        self.end_headers()

class OperationServer(object):
    def __init__(self, serverAddress, port):
        self.serverAddress = (serverAddress, port)
        self.httpd = http.server.HTTPServer(self.serverAddress, OperationServerHandler)

    def run(self):
        self.httpd.serve_forever()

    def cleanup(self):
        self.httpd.shutdown()

if __name__ == '__main__':

    # Parse Args
    port = int(sys.argv[1])
    address = ''
    try:
        address = sys.argv[2]
    except:
        pass

    webserver = OperationServer(address, port)

    global Learner
    Learner = None

    try:
        webserver.run()
    except KeyboardInterrupt:
        webserver.cleanup()
        Learner.Conclude()
    except:
        webserver.cleanup()
        Learner.Conclude()