import os
import sys
sys.path.insert(0, os.getcwd())
sys.path.insert(0, '../../')

import math
import numpy as np
import agents
import agents.framework_AgentServer
import agents.kerasMLs
import mdp as mdplib

# Some constants from Park and Pensieve's reward functions
M_IN_K = 1000.0
VIDEO_BIT_RATE = [300,750,1200,1850,2850,4300]  # Kbps
AgentCount = 1
LinkQuality = 12000000
# number of milliseconds to consider something as "cached" rather than downloaded
CacheThreshold = 20


class ABRControllerExperimentModule(mdplib.PartialMDPModule):

    def __init__(self, loggingDirPath, logFileName, agentCount:int=None):

        self.AgentCount = agentCount

        # Defining the MDP
        mdp = []

        # "lower" performance state 0
        mdp.append(mdplib.State([lambda a: self.DefineReward(a, a) <= 16.5], [0]))

        # "ambiguous" performance state 1
        mdp.append(mdplib.State([lambda a: self.DefineReward(a, a) > 16.5 and self.DefineReward(a, a) <= 19], [2,3,4,5]))

        # "high end" performance state 2
        mdp.append(mdplib.State([lambda a: self.DefineReward(a, a) > 19], [4,5]))

        # Hold the history of some inputs
        self.history = dict()
        self.history['last_total_rebuf'] = 0
        # Default initial bitrate index
        self.history['last_bit_rate'] = 0

        super().__init__(mdp=mdp, logPath=loggingDirPath, logFileName=logFileName, actionSpace=[0,1,2,3,4,5])

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
        """Reward function as outlined by Park and Pensieve: --linear reward-- """

        if 'RebufferTime' not in rawObservation.keys():
            return None

        SMOOTH_PENALTY = 1
        REBUF_PENALTY = 4.3  # 1 sec rebuffering -> this number of Mbps

        print('Obv: {}'.format(rawObservation))

        rebuffer_time = float(rawObservation['RebufferTime'] - self.history['last_total_rebuf'])

        reward = VIDEO_BIT_RATE[rawObservation['lastquality']] / M_IN_K - REBUF_PENALTY * rebuffer_time / M_IN_K - SMOOTH_PENALTY * np.abs(VIDEO_BIT_RATE[rawObservation['lastquality']] - self.history['last_bit_rate']) / M_IN_K

        self.history['last_bit_rate'] = VIDEO_BIT_RATE[rawObservation['lastquality']]
        self.history['last_total_rebuf'] = rawObservation['RebufferTime']

        # fairness "violation"

        # DownloadTime in milliseconds
        downLoadTime = rawObservation['lastChunkFinishTime'] - rawObservation['lastChunkStartTime']

        if downLoadTime <= CacheThreshold:
            # cached?
            downLoadTime = -1

        # Chunksize is in bytes

        if self.AgentCount is not None:

            # bandwidth consumed in bits/millisecond
            bandwidthConsumed = rawObservation['lastChunkSize'] * 8 / downLoadTime

            # bandwidth estimate is in bits/? convert to per millisecond
            estimatedAllowance = rawObservation['bandwidthEst']/self.AgentCount

            evalReward, fairness = agents.CoreReward(throughputMbps=bandwidthConsumed/1000, timeCompletionSeconds=downLoadTime/1000,allowedBandwidthMbps=estimatedAllowance/1000,fairnessWeight=0.75)

            rawObservation['chunk-download-time-millisecond'] = downLoadTime
            rawObservation["bandwidth-consumed-bits-per-millisecond"] = bandwidthConsumed * 1000
            rawObservation["estimated-bandwidth-allowance-bits-per-millisecond"] = estimatedAllowance
            rawObservation["fairness"] = fairness
            rawObservation["eval-reward"] = evalReward

        return reward


if __name__ == '__main__':

    # Parse the default args
    args = agents.framework_AgentServer.ParseDefaultServerArgs()

    # Setup domain definition
    if 'AgentCount' in args:
        domainDF = ABRControllerExperimentModule(args['AgentDir'] + args['LogPath'], args['LogFileName'], args['AgentCount'])
    else:
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