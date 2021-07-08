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

# Basic Python Web Server with contents

# Running Parameters
# Web Content Dir
# Port


def PrepCall(webContentDir:str, port:int) -> list:

    return []


class HTTPServerPython(apps.App):

    def ParseOutput(self, rawData:bytes, args:dict) -> dict:

        return {}

    def Run(self, args:dict) -> dict:

        cmdArgs = apps.ToPopenArgs(args)

        command = ['python3']
        command.extend(cmdArgs)

        outputRaw = subprocess.check_output(command, stderr=subprocess.STDOUT)

        output = self.ParseOutput(outputRaw, args)

        # Add the action args
        output.update(args)

        return output


if __name__ == '__main__':

    apps.RunApplication(HTTPServerPython())
