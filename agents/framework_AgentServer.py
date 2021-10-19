import os
import sys
import json
import http.server
from typing import Tuple
import signal
import agents


# Abstractions for Agent

class AgentArgs(object):

    def __init__(self
                 , agentDir='./tmp/'
                 , agentPort=8080
                 , training=1
                 , logPath:str=""
                 , logFileName:str=""
                 , miscArgs:dict=None):
        """The abstraction of a 'learner' comprised of a ml module, problem definition,
         and a server to host on. Intended to call a learner's setup script in /agents/ and pass some args."""
        self.AgentPort = agentPort
        self.AgentDir = agentDir
        self.Training = training
        self.LogPath = logPath
        self.LogFileName = logFileName
        self.MiscArgs = miscArgs

    def ToArgs(self) -> dict:

        rawArgs = self.__dict__.copy()

        del rawArgs['MiscArgs']

        rawArgs.update(self.MiscArgs)

        return rawArgs


# Agent Server (Agent implementation)

def ParseDefaultServerArgs() -> dict:
    """Parse the default Agent Server args: port, address, mode, learnerDir, logPath"""
    # expects a full json object passed
    args = json.loads(sys.argv[1])

    print('Agent: Args {}'.format(args))

    # Setup the agent directory
    try:
        os.makedirs(args['AgentDir'], exist_ok=True)
    except Exception as ex:
        print('Agent-Server: Error making dirs: {}'.format(ex))

    return args


class AgentHttpHandler(http.server.SimpleHTTPRequestHandler):

    def do_POST(self):
        """Receives observations from the environment, then responds with the next action that should be taken"""
        # Parse out necessary parameters
        length = int(self.headers['content-length'])
        postDataRaw = self.rfile.read(length)

        # Convert from POST to dict
        rawObservation = json.loads(postDataRaw)

        # Process the info through the domain definition
        server:AgentServer = self.server

        obv, reward, done, info = server.DomainModule.Process(rawObservation)

        totalActionSpace = server.DomainModule.DefineActionspace(rawObservation, obv)

        actionSpaceSubset = server.DomainModule.DefineActionspaceSubset(rawObservation, obv)

        selectedAction = server.LogicModule.Operate(obv, reward, totalActionSpace, actionSpaceSubset, info)

        action = totalActionSpace[selectedAction]

        # Convert commands to Json
        returnCommandsJson = json.dumps(action, indent=5)

        # set HTTP headers
        self.send_response(200)
        self.send_header('Content-Type', 'text/plain')
        self.send_header('Content-Length', str(len(returnCommandsJson)))
        self.send_header('Access-Control-Allow-Origin', "*")

        self.end_headers()

        # Finish web transaction
        self.wfile.write(returnCommandsJson.encode())


class AgentServer(http.server.HTTPServer):

    def __init__(self, domainModule:agents.DomainModule, logicModule:agents.LogicModule, server_address: Tuple[str, int]):
        """ML HTTP Server, will stand as endpoint to receive observations
        from environment and send out actions as response to requests."""
        super().__init__(server_address, AgentHttpHandler)

        # Indicate that sigterm should call shutdown of the server
        signal.signal(signal.SIGTERM, self.Cleanup)
        signal.signal(signal.SIGINT, self.Cleanup)

        self.DomainModule = domainModule
        self.LogicModule = logicModule

    def Cleanup(self):

        # Shutdown the server
        self.shutdown()

        # Handle the module's conclusions
        self.LogicModule.Conclude()
        print('Agent Server: Shuting down')

    def Run(self):

        try:
            self.serve_forever()
        except KeyboardInterrupt:
            print()
        except Exception as ex:
            print(str(ex))
        finally:
            self.Cleanup()
