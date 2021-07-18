import subprocess
import numpy as np
import json
import time

# Setup the dir
DirOffset = '../../'

import os
import sys

sys.path.insert(0, os.getcwd())
sys.path.insert(0, DirOffset)
# Hack for overcoming some dir issues

import apps


class Iperf3App(apps.App):

    def TranslateActions(self, args:dict) -> (dict, list):

        translatedActions = dict()

        self.TranslateAction('-target-server-address', args, '-c', translatedActions)

        if '-logfile' in args.keys():
            translatedActions['--logfile'] = args['-logfile']

        if '-parallel-tcp' in args.keys():
            translatedActions['-P'] = args['-parallel-tcp']

        if '-tcp-congestion-control' in args.keys():
            translatedActions['-C'] = args['-tcp-congestion-control']

        if '-target-request-port' in args.keys():
            translatedActions['-p'] = args['-target-request-port']

        if '-run-duration-seconds' in args.keys():
            translatedActions['-t'] = args['-run-duration-seconds']

        return translatedActions, None

    def Run(self, runArgs:dict) -> (dict, list):

        # check if outputing to log file, if so must do indexing to prevent overwrites
        if '--logfile' in runArgs.keys():
            runArgs['--logfile'] = runArgs['--logfile']

        cmdArgs = apps.ToPopenArgs(runArgs)

        command = ['iperf3']
        command.extend(cmdArgs)

        # output to Json for easier parsing
        if '-J' not in command:
            command.append('-J')

        outputRaw = subprocess.check_output(command, stderr=subprocess.STDOUT)

        output = apps.ParseIperf3Output(outputRaw, runArgs)

        if '-C' not in command:
            output['-tcp-congestion-control'] = apps.getCC()

        return output, []


# Allow call to just run iperf with initial args
if __name__ == '__main__':

    apps.RunApplication(Iperf3App())

