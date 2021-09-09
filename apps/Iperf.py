import json
import time
import numpy as np
import subprocess

# Setup the dir
DirOffset = '../../'

import os
import sys
sys.path.insert(0, os.getcwd())
sys.path.insert(0, DirOffset)
# Hack for overcoming some dir issues
# https://serverfault.com/questions/566737/iperf-csv-output-format

import apps
import apps.framework_DMF


class IperfApp(apps.App):

    def ParseOutput(self, rawData:bytes) -> dict:

        outputRaw = rawData.decode()

        outputLines = outputRaw.split('\n')

        # Take the sum line
        output = outputLines[-2].split(',')

        dataDict = dict()

        if len(outputRaw) <= 0:
            raise Exception('No Iperf output')

        dataDict.update(apps.framework_DMF.TimeStampDMF(value=output[0], unit='date-time',
                                     traits=['application-level',
                                             'day-of-week, day month-abbreviated year, hour:minute:second GMT']).ToDict())

        dataDict['source_addr'] = output[1]
        dataDict['source_port'] = output[2]

        dataDict.update(apps.framework_DMF.TargetAddressDMF(value=output[3], unit='IP',traits=['application-level']).ToDict())
        dataDict.update(apps.framework_DMF.TargetPortDMF(value=int(output[4]), unit='Port',traits=['application-level']).ToDict())

        dataDict.update(apps.framework_DMF.PollRateDMF(value=float(output[6]), unit='second',traits=['application-level']).ToDict())

        dataDict.update(apps.framework_DMF.DataReceivedDMF(value=int(output[7]), unit='byte',
                                    traits=['receiver', 'application-level']).ToDict())

        dataDict.update(apps.framework_DMF.ThroughputDMF(value=float(output[8]), unit='bits-per-second',
                                      traits=['application-level', 'receiver']).ToDict())

        return dataDict

    def TranslateActions(self, args:dict) -> (dict, list):

        translatedActions = dict()

        if '-parallel-tcp' in args.keys():
            translatedActions['-P'] = args['-parallel-tcp']

        if '-tcp-congestion-control' in args.keys():
            translatedActions['-Z'] = args['-tcp-congestion-control']

        if '-target-request-port' in args.keys():
            translatedActions['-p'] = args['-target-request-port']

        if '-run-duration-seconds' in args.keys():
            translatedActions['-t'] = args['-run-duration-seconds']

        return translatedActions

    def Run(self, runArgs:dict) -> (dict, list):

        cmdArgs = apps.ToPopenArgs(runArgs)

        command = ['iperf']
        command.extend(cmdArgs)

        # format into csv for easier parsing
        if '-y' not in command:
            command.append('-y')
            command.append('C')

        outputRaw = subprocess.check_output(command)

        output = self.ParseOutput(outputRaw)

        if '-Z' not in command:
            output['-tcp-congestion-control'] = apps.getCC()

        return output, None


# Allow call to just run iperf with initial args
if __name__ == '__main__':

    apps.RunApplication(IperfApp())

