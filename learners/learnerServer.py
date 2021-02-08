import sys
import json
import http.server
from typing import Tuple
import signal
import learners


def loadPatternFile(patternPath:str) -> list:
    """Loads a csv file in for use by pattern module"""
    patternFP = open(patternPath, 'r')
    patternPieces = patternFP.readlines()

    patternPieces[0] = patternPieces[0].replace('\n', '')

    patternFields = patternPieces[0].split(',')

    pattern = []

    for line in patternPieces[1:]:
        patternDict = dict()

        line = line.replace('\n', '')

        linePieces = line.split(',')

        for idx, piece in enumerate(linePieces):
            patternDict[patternFields[idx]] = piece

        pattern.append(patternDict)

    patternFP.close()

    return pattern


def ParseDefaultServerArgs():

    port = int(sys.argv[1])
    learnerAddress = sys.argv[2]
    mode = int(sys.argv[3])
    learnerDir = sys.argv[4]
    traceFilePostFix = sys.argv[5]
    miscArgs = None
    if len(sys.argv) >= 6:
        miscArgs = sys.argv[6:]

    print('Learner: Server args: {} {} {} {} {} {}'.format(port, learnerAddress, mode, learnerDir, traceFilePostFix, miscArgs))

    return port, learnerAddress, mode, learnerDir, traceFilePostFix, miscArgs


class MLHttpHandler(http.server.SimpleHTTPRequestHandler):

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

    def __init__(self, domainDefinition:learners.DomainModule, mlModule, server_address: Tuple[str, int]):
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

    def Run(self):

        try:
            self.serve_forever()
        except KeyboardInterrupt:
            print()
        except Exception as ex:
            print(str(ex))
        finally:
            self.Cleanup()
