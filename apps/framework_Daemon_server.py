import subprocess
import http.server
import time
import json
import sys
import os

# Server for running/stopping/checking on apps running on hosts started by this server
# Get will advertise the testing application's status, running, time running, application executing, etc

global ApplicationProcs
# Processes are described by name of process, parameters, and
ApplicationProcs = []

ProcessIDFieldLabel = 'processID'
ProcessArgsFieldLabel = 'args'

CommandDescriptions = {
    '/processInfo/':    'optional <processID>',
    '/processStart/':   '<args>',
    '/processStop/':    'optional <processID>'
}

def PrepareServerArgs(dirOffset='./', opServerPort=8081):
    '''
    Returns list of args for use in Popen()

            Parameters:
                    dirOffset (str): Path to get to the root directory of the project. for python use
                    opServerPort (int): Port to listen for incoming operation calls

            Returns:
                    argList (list): List of args for use in Popen()
    '''
    return ['python3', '{}apps/framework_Daemon_server.py'.format(dirOffset), '{}'.format(opServerPort)]


class DaemonServerHandler(http.server.SimpleHTTPRequestHandler):

    # GET Report the status of the running application(s)
    def do_GET(self):
        global ApplicationProcs

        requestTimeStart = time.time()

        print(self.path)

        # load in the asset
        itemPath = self.path

        # browser agent
        browser = self.headers['User-Agent']

        # http version
        httpVersion = self.protocol_version

        # set the headers
        self.send_response(200)
        self.end_headers()

        # Describe the processes
        dataDict = dict()

        dataDict.update(CommandDescriptions)
        dataDict['CWD'] = os.getcwd()

        for index, proc in enumerate(ApplicationProcs):
            procName = proc.args
            proc.poll()
            procReturnCode = proc.returncode
            dataDict['process-{}-{}-returnCode'.format(index, procName)] = procReturnCode

        jsonDescription = json.dumps(dataDict, indent=5)

        self.wfile.write(jsonDescription.encode())

        requestTimeEnd = time.time()

        requestCompletionTime = requestTimeEnd - requestTimeStart

    # POST - Receive commands to execute
    def do_POST(self):

        global ApplicationProcs

        itemPath = self.path

        # Parse out necessary parameters
        length = int(self.headers['content-length'])
        postDataRaw = self.rfile.read(length)

        # Convert from POST to dict
        stateData = {}

        if postDataRaw is not None and length > 0:
            stateData = json.loads(postDataRaw)

        # Return data
        dataDict = {}

        processID = None
        args = None

        if ProcessIDFieldLabel in stateData.keys():
            # has processID
            processID = stateData[ProcessIDFieldLabel]

        if ProcessArgsFieldLabel in stateData.keys():
            args = stateData[ProcessArgsFieldLabel]

        # Parse the args from the POST
        # select based on action
        if itemPath in '/processInfo/':

            if processID is None:
                for index, proc in enumerate(ApplicationProcs):
                    procName = proc[0]
                    procRunning = proc[1]
                    procReturnCode = procRunning.returncode
                    dataDict['process-{}-{}'.format(index, procName)] = procReturnCode
            else:

                if processID <= len(ApplicationProcs):
                    proc = ApplicationProcs[processID]
                    procName = proc[0]
                    procRunning = proc[1]
                    procReturnCode = procRunning.returncode
                    dataDict['process-{}'.format(procName)] = procReturnCode
                else:
                    dataDict['ERROR'] = 'No process of that ID passed'

        elif itemPath in '/processStart/':

            if args is not None:
                ApplicationProcs.append(subprocess.Popen(args))
            else:
                dataDict['ERROR'] = 'No args passed'

        elif itemPath in '/processStop/':

            if processID is not None:
                proc = ApplicationProcs[processID]
                proc.kill()
                proc.wait(timeout=10)
                del ApplicationProcs[processID]
            else:
                print('Daemon Server: Killing {} procs'.format(len(ApplicationProcs)))
                for index, proc in enumerate(ApplicationProcs):
                    print('Daemon Server: attempt to kill {}'.format(proc))
                    proc.kill()
                    proc.wait(timeout=10)
                    print('Daemon Server: {} killed'.format(proc))

                ApplicationProcs.clear()
        else:
            dataDict['ERROR'] = 'No matching command'

        # Convert commands to Json
        returnCommandsJson = json.dumps(dataDict, indent=5)

        # set HTTP headers
        self.send_response(200)
        self.end_headers()

        # Finish web transaction
        self.wfile.write(returnCommandsJson.encode())


class DaemonServer(object):
    def __init__(self, serverAddress, port):
        self.serverAddress = (serverAddress, port)
        self.httpd = http.server.HTTPServer(self.serverAddress, DaemonServerHandler)

    def run(self):
        self.httpd.serve_forever()

    def cleanup(self):
        self.httpd.shutdown()

        for index, proc in enumerate(ApplicationProcs):
            proc.kill()
            proc.wait()
            print('Daemon Server: {} killed'.format(proc))

        ApplicationProcs.clear()


if __name__ == '__main__':

    port = int(sys.argv[1])
    address = ''
    try:
        address = sys.argv[2]
    except:
        pass

    # ==============================

    daemonServer = DaemonServer(address, port)

    # 0.0.0.0 means listen on any address, stating localhost breaks it for external connections
    print('Daemon Server: http://{}:{}/ {}'.format(address, port, os.getcwd()))

    try:
        daemonServer.run()
    except KeyboardInterrupt:
        print()
    except Exception as ex:
        print(str(ex))
    finally:
        daemonServer.cleanup()
        print('Daemon Server: Cleaned up')