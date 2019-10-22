import os
import glob
import subprocess
import time
import json
import shutil
from datetime import datetime
import numpy as np

class server:

    def __init__(self, network, client):
        self.LogFilePath = './tmp/epoch-server-Log.json'
        self.Command = ['iperf3', '-s', '-J', '--logfile', self.LogFilePath]
        self.process = None
        self.Network = network
        self.Client = client

    def setup(self):
        pass

    def run(self):
        # update run args

        # remove the old log
        try:
            os.remove(self.LogFilePath)
        except:
            pass

        self.process = subprocess.Popen(self.Command)

    def shutdown(self):
        self.process.kill()
        self.process.wait()

    def log(self):

        # load the log file
        serverLogFileDS = open(self.LogFilePath, 'r')

        serverLogRawLines = serverLogFileDS.readlines()

        serverLogFileDS.close()

        rawWholeLine = ''

        for rawLine in serverLogRawLines:
            rawWholeLine = rawWholeLine + rawLine

        #json.loads(rawWholeLine)
        # load raw string into json dict

        jsonbody = ''

        if len(rawWholeLine) > 1:

            rawJson = '{\"setup\": {}, \"logs\":' + rawWholeLine + '}'

            jsonbody = json.loads(rawJson)

        #os.remove(self.LogFilePath)

        # output the logs

        return jsonbody


    # EDITABLE - Visualize/Graph/Human readable
    def report(self):

        pass