import subprocess
import netifaces
import socket
import os

class client:

    def __init__(self, network, server):
        # number of Iperf servers to start up
        self.ParallelTCPConnections = 1
        self.RunTime = 10
        # must be updated
        self.TargetServerIP = '10.131.229.161'
        self.LogFilePath = './tmp/epoch-client-Log.txt'
        self.Command = ['iperf3', '-c', self.TargetServerIP, '--logfile', self.LogFilePath, '-t', str(self.RunTime), '-R',
                        '-P', str(self.ParallelTCPConnections)]
        self.process = None
        self.Network = network
        self.Server = server

    def setup(self):
        self.Command[2] = self.TargetServerIP
        self.Command[6] = str(self.RunTime)
        self.Command[9] = str(self.ParallelTCPConnections)

    def run(self):
        # update the run args
        #self.process = subprocess.Popen(self.Command)
        # Wait to end
        #self.process.wait()
        # remove the old log
        try:
            os.remove(self.LogFilePath)
        except:
            pass

    def shutdown(self):
        #self.process.kill()
        #self.process.wait()
        pass

    def log(self):

        # load and parse the created log file, it is in raw text form
        logFileDS = open(self.LogFilePath, 'r')

        logFileLinesRaw = logFileDS.readlines()

        logFileDS.close()

        for rawLine in logFileLinesRaw:
            if 'sender' in rawLine:
                # sender summary line
                pass
            elif 'receiver' in rawLine:
                # receiver summary line
                pass

        # adjust the logs
        jsonBody = {'setup': {'parallelTCPConnections': self.ParallelTCPConnections,
                              'runTime': self.RunTime,
                              'targetIP': self.TargetServerIP},
                    'logs': {}
                    }

        # output log file
        #os.remove(self.LogFileFullPath)

        return jsonBody

    # EDITABLE - Visualize/Graph/Human readable
    def report(self):

        pass