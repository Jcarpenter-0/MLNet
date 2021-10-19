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
LinkQuality = 12000000
# number of milliseconds to consider something as "cached" rather than downloaded
CacheThreshold = 20


class ABRControllerExperimentModule(agents.DomainModule):

    def __init__(self, loggingDirPath, logFileName, agentCount:int=None):
        self.AgentCount = agentCount
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
        estimatedAllowance = rawObservation['bandwidthEst']/self.AgentCount

        reward, fairness = agents.CoreReward(throughputMbps=bandwidthConsumed/1000, timeCompletionSeconds=downLoadTime/1000,allowedBandwidthMbps=estimatedAllowance/1000
                                             , fairnessWeight=0.75)

        rawObservation['chunk-download-time-millisecond'] = downLoadTime
        rawObservation["bandwidth-consumed-bits-per-millisecond"] = bandwidthConsumed * 1000
        rawObservation["estimated-bandwidth-allowance-bits-per-millisecond"] = estimatedAllowance
        rawObservation["fairness"] = fairness

        return reward


if __name__ == '__main__':

    # Parse the default args
    args = agents.framework_AgentServer.ParseDefaultServerArgs()

    # Setup domain definition
    domainDF = ABRControllerExperimentModule(args['AgentDir'] + args['LogPath'], args['LogFileName'])

    # Depending on mode
    if args['Training'] == 1 or args['Training'] == 0:
        # training/testing
        mlModule = agents.kerasMLs.kerasActorCritic(args['AgentDir'], 7, len(domainDF.ActionSpace))
    else:

        mlModule = agents.RepeatModule()

    # Declare a server
    server = agents.framework_AgentServer.AgentServer(domainDF, mlModule, ('', args['AgentPort']))

    server.Run()