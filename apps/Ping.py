import numpy as np
import subprocess

# Setup the dir
DirOffset = '../../'

import os
import sys
sys.path.insert(0, os.getcwd())
sys.path.insert(0, DirOffset)
# Hack for overcoming some dir issues
import apps


class PingApp(apps.App):

    def DefineMetrics(self) -> dict:
        """Defines what metrics this application provides. Result is dict with metric name and metric info."""
        metricDict = dict()

        metricDict['targetURL'] = str
        metricDict['targetIP'] = str
        metricDict['packetBytes'] = int
        metricDict['packetBytesActual'] = int
        metricDict['packetsTransmitted'] = int
        metricDict['packetsReceived'] = int
        metricDict['packetLoss'] = float
        metricDict['time'] = int
        metricDict['rttMin'] = float
        metricDict['rttAvg'] = float
        metricDict['rttMax'] = float
        metricDict['rttMdev'] = float

        return metricDict

    def DefineActions(self) -> dict:
        """Return a dict of each input parameter with the range of values it can have. \n
        Example, ('para1':range(0,5))"""
        actionDict = dict()

        actionDict['-c'] = range(1, 89887899511685119)
        actionDict['-i'] = np.arange(0.2, 2147482, 0.1)
        actionDict['-s'] = range(56, 65507)
        actionDict['-t'] = range(1, 255)

        return actionDict

    def ParsePingOutput(self, rawData:bytes) -> dict:

        output = rawData.decode()

        # Parse the data from it
        dataDict = dict()

        pingOutputLines = output.split('\n')

        inputLine = pingOutputLines[0].split(' ')

        dataDict['targetURL'] = inputLine[1]
        dataDict['targetIP'] = inputLine[2]
        dataDict['packetBytes'] = int(inputLine[3].split('(')[0])
        dataDict['packetBytesActual'] = int(inputLine[3].split('(')[1].replace(')',''))

        packetLine = pingOutputLines[3].split(' ')
        dataDict['packetsTransmitted'] = int(packetLine[0])
        dataDict['packetsReceived'] = int(packetLine[3])
        dataDict['packetLoss'] = float(packetLine[5].replace('%', ''))
        dataDict['time'] = int(packetLine[-1].replace('ms', ''))

        statLine = pingOutputLines[4].split(' ')[3].split('/')

        dataDict['rttMin'] = float(statLine[0])
        dataDict['rttAvg'] = float(statLine[1])
        dataDict['rttMax'] = float(statLine[2])
        dataDict['rttMdev'] = float(statLine[3])

        return dataDict

    def Run(self, runArgs:dict) -> dict:
        cmdArgs = apps.ToPopenArgs(runArgs)

        command = ['ping']
        command.extend(cmdArgs)

        # Quiet the output for easier parsing
        if '-q' not in command:
            command.append('-q')

        print(command)

        outputRaw = subprocess.check_output(command)

        output = self.ParsePingOutput(outputRaw)

        # Add the action args
        output.update(runArgs)

        return output


# Allow call to just run iperf with initial args
if __name__ == '__main__':

    apps.RunApplication(PingApp())
