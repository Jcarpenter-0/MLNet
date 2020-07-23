import http.server
import json
import time
import sys
import requests
import mimetypes
import os

# Global Webserver Reference
Webserver = None

class CustomHandler(http.server.SimpleHTTPRequestHandler):

    def do_GET(self):

        logDict = dict()

        requestTimeStart = time.time()
        logDict['requestStart'] = requestTimeStart

        # based on asset type, change cc
        print(self.path)

        # load in the asset
        itemPath = self.path

        logDict['assetPath'] = itemPath

        assetFP = open(itemPath, 'rb')

        assetData = assetFP.readlines()

        assetFP.close()

        # asset size bytes
        logDict['assetSize'] = os.path.getsize(itemPath)

        # asset type
        logDict['mimeType'] = mimetypes.read_mime_types(itemPath)

        # browser agent
        logDict['userAgent'] = self.headers['User-Agent']

        # http version
        logDict['httpVersion'] = self.protocol_version

        self.send_response(200)
        self.end_headers()

        self.wfile.writelines(assetData)

        requestTimeEnd = time.time()

        logDict['requestTime'] = requestTimeEnd - requestTimeStart

        # send data to learner
        Webserver.sendToLearner(logDict)


class HttpWebServer():

    def __init__(self, address, port, learner):
        self.serverAddress = (address, port)
        self.httpd = http.server.HTTPServer(self.serverAddress, CustomHandler)
        self.LearnerTarget = learner

        # Fake buffer, just holds references to objects, if in cache, considered a "hit"
        # If not, considered a miss
        self.FakeBuffer = dict()

    def sendToLearner(self, data):
        # Prune from the dict what you only want to send
        sendDict = dict()

        sendDict['bps-1'] = data['end']['sum_sent']['bits_per_second']
        sendDict['retransmits-1'] = data['end']['sum_sent']['retransmits']
        sendDict['bps-0'] = data['bps-0']
        sendDict['retransmits-0'] = data['retransmits-0']

        # Send action info
        for actionIndex in range(0, 1):

            if prevActionID == actionIndex:
                sendDict['actionID-{}'.format(actionIndex)] = 1
            else:
                sendDict['actionID-{}'.format(actionIndex)] = 0

        # Encode from dict to JSON again
        jsonData = json.dumps(sendDict)

        # Update the start vector
        StartVector['bps-0'] = sendDict['bps-1']
        StartVector['retransmits-0'] = sendDict['retransmits-1']

        # Send to learner, and get new action
        print('Sending {}'.format(sendDict))

        response = requests.post(learner, data=jsonData)

        respDict = json.loads(response.content.decode())

        # Convert action to paras
        newActionID = int(respDict['actionID'])

        print('Recieved ActionID {}'.format(newActionID))

    def run(self):
        self.httpd.serve_forever()

    def cleanup(self):
        self.httpd.shutdown()


if __name__ == '__main__':
    port = int(sys.argv[1])
    address = ''
    try:
        address = sys.argv[2]
    except:
        pass

    # Get learner endpoint
    learner = None
    try:
        learner = sys.argv[3]
    except:
        pass

    Webserver = HttpWebServer(address, port, learner)

    try:
        Webserver.run()
    except KeyboardInterrupt:
        print()
    except Exception as ex:
        print()
    finally:
        Webserver.cleanup()