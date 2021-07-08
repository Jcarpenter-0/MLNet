import os
import sys
import json
import http.server
from typing import Tuple
import signal
import agents


# Abstractions for Agent

class AgentWrapper(object):

    def __init__(self, agentScriptPath
                 , agentDir='./tmp/'
                 , agentPort=8080
                 , training=1
                 , logPath:str=None
                 , miscArgs:list=None):
        """The abstraction of a 'learner' comprised of a ml module, problem definition,
         and a server to host on. Intended to call a learner's setup script in /agents/ and pass some args."""
        self.LearnerScriptPath = agentScriptPath
        self.LearnerPort = agentPort

        self.LearnerDir = agentDir
        self.Training = training

        self.BaseCommand = ['python3', '{}'.format(self.LearnerScriptPath)]

        self.LogPath = logPath
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
            , self.LogPath
        ])

        if self.MiscArgs is not None:
            commandArgs.extend(self.MiscArgs)

        return commandArgs


# Agent Server (Agent implementation)

def ParseDefaultServerArgs() -> (int, str, int, str, str, list):
    """Parse the default Agent Server args: port, address, mode, learnerDir, logPath"""
    port = int(sys.argv[1])
    learnerAddress = sys.argv[2]
    mode = int(sys.argv[3])
    learnerDir = sys.argv[4]
    logPath = sys.argv[5]

    miscArgs = None
    if len(sys.argv) >= 6:
        miscArgs = sys.argv[6:]

    print('Agent: Server args: {}'.format(sys.argv))

    # Setup the learnerDir
    try:
        os.makedirs(learnerDir, exist_ok=True)
    except Exception as ex:
        print('Agent-Server: Error making dirs: {}'.format(ex))

    return port, learnerAddress, mode, learnerDir, logPath, miscArgs


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

        self.DomainModule = domainModule
        self.LogicModule = logicModule

    def Cleanup(self):

        # Shutdown the server
        self.shutdown()

        # Handle the module's conclusions
        self.LogicModule.Conclude()

    def Run(self):

        try:
            self.serve_forever()
        except KeyboardInterrupt:
            print()
        except Exception as ex:
            print(str(ex))
        finally:
            self.Cleanup()
