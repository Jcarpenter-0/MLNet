import subprocess

# Setup the dir
DirOffset = '../../'

import os
import sys
sys.path.insert(0, os.getcwd())
sys.path.insert(0, DirOffset)
# Hack for overcoming some dir issues

import psutil
import apps
import apps.additionalDMFs.videostreaming
import time


def PrepCall(targetServerAddress:str, targetServerPort:int,
                           agentServerAddress:str=None, agentServerPort:int=None,
                           probingApproach:int=None, probingInterface:str=None, runDuration:int=None,
                           protocol:str=None, parallelTCPConnections:int=None, logFilePath:str=None) -> list:

    commands = apps.PrepGeneralWrapperCall('apps/abr_client_simulated.py',
                                           targetServerAddress, targetServerPort, agentServerAddress, agentServerPort,
                                           probingApproach, probingInterface, runDuration, protocol, parallelTCPConnections,
                                           logFilePath)

    return commands


class AdaptiveBitRateVideoStreamingSimulator(apps.App):

    def __init__(self, bufferCapacity:apps.DescriptiveMetricFormat=apps.BufferSizeDMF(unit='second', traits=['buffer-time'])):
        super().__init__()
        self.BufferCapacity = bufferCapacity
        self.BufferContents = 0

    def Run(self, args:dict) -> dict:
        """Simple Video Streaming System, fill buffer, empty buffer"""

        return {}


if __name__ == '__main__':

    apps.RunApplication(AdaptiveBitRateVideoStreamingSimulator())
