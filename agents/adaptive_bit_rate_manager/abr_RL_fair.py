import os
import sys
sys.path.insert(0, os.getcwd())
sys.path.insert(0, '../../')

import math
import numpy as np
import agents
import agents.framework_AgentServer
import agents.kerasMLs


# Some constants from Park and Pensieve's reward functions
M_IN_K = 1000.0
VIDEO_BIT_RATE = [300,750,1200,1850,2850,4300]  # Kbps
AgentCount = 1
LinkQuality = 12000000
# number of milliseconds to consider something as "cached" rather than downloaded
CacheThreshold = 20


class ABRControllerExperimentModule(agents.DomainModule):

    def __init__(self, loggingDirPath):
        super().__init__(logPath=loggingDirPath, logFileName=logFileName, actionSpace=[0,1,2,3,4,5])

    def DefineObservation(self, rawObservation:dict) -> list:

        desiredFields = ['lastquality'
            ,'buffer'
            ,'bandwidthEst'
            ,'RebufferTime'
            ,'lastChunkFinishTime'
            ,'lastChunkStartTime'
            ,'lastChunkSize']

        observation = []

        for value in desiredFields:
            observation.append(rawObservation[value])

        return observation

    def DefineReward(self, observation, rawObservation):

        # fairness "violation"

        # DownloadTime in milliseconds
        downLoadTime = rawObservation['lastChunkFinishTime'] - rawObservation['lastChunkStartTime']

        if downLoadTime <= CacheThreshold:
            # cached?
            downLoadTime = -1

        # bandwidth consumed in bits/millisecond
        bandwidthConsumed = rawObservation['lastChunkSize'] * 8 / downLoadTime

        # Chunksize is in bytes

        # bandwidth estimate is in bits/? convert to per millisecond
        estimatedAllowance = rawObservation['bandwidthEst']/AgentCount

        reward, unfairness = agents.CoreReward(throughputMbps=bandwidthConsumed/1000, timeCompletionSeconds=downLoadTime/1000,allowedBandwidthMbps=estimatedAllowance/1000)

        rawObservation['chunk-download-time-millisecond'] = downLoadTime
        rawObservation["bandwidth-consumed-bits-per-millisecond"] = bandwidthConsumed
        rawObservation["estimated-bandwidth-allowance-bits-per-millisecond"] = estimatedAllowance
        rawObservation["fairness"] = unfairness

        return reward


if __name__ == '__main__':

    # Parse the default args
    port, address, mode, learnerDir, loggingPath, logFileName, miscArgs = agents.framework_AgentServer.ParseDefaultServerArgs()

    # Setup domain definition
    domainDF = ABRControllerExperimentModule(learnerDir + loggingPath)

    # Depending on mode
    if mode == 1 or mode == 0:
        # training/testing
        mlModule = agents.kerasMLs.kerasActorCritic(learnerDir, 7, len(domainDF.ActionSpace))
    else:

        mlModule = agents.RepeatModule()

    # Declare a server
    server = agents.framework_AgentServer.AgentServer(domainDF, mlModule, (address, port))

    server.Run()