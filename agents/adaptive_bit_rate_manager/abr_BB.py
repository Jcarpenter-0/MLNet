import os
import sys
sys.path.insert(0, os.getcwd())
sys.path.insert(0, '../../')

import numpy as np
import agents
import agents.framework_AgentServer


# Some constants from Park and Pensieve's reward functions
M_IN_K = 1000.0
VIDEO_BIT_RATE = [300,750,1200,1850,2850,4300]  # Kbps


class BufferBasedDecisionLogic(agents.LogicModule):

    def __init__(self):
        """Implementing the Buffer Based (BB) Adaptive Bit Rate Algorithm: Described and partially copied from: Neural Adaptive Video Streaming with Pensieve"""
        self.Cushion = 10
        self.Resevoir = 5
        super().__init__()

    def Operate(self, observation, reward, actionSpace, actionSpaceSubset, info):
        """Quoting from Pensieve paper: uses a reservoir of 5 seconds and a cushion of 10 seconds,
         i.e., it selects bitrates with the goal of keeping the buffer occupancy above 5 seconds, and automatically
         chooses the highest available bitrate if the buffer occupancy exceeds 15 seconds."""

        selectedBitRateIndex = 0

        if 'buffer' in info.keys():

            if info['buffer'] < self.Resevoir:
                selectedBitRateIndex = 0
            elif info['buffer'] >= self.Resevoir + self.Cushion:
                selectedBitRateIndex = len(actionSpace) - 1
            else:
                selectedBitRateIndex = (len(actionSpace) - 1) * (info['buffer'] - self.Resevoir) / float(self.Cushion)

            print('ABR Logic Module Buffer Based: Selected Bitrate: {}'.format(int(selectedBitRateIndex)))

        return int(selectedBitRateIndex)


class ABRControllerExperimentModule(agents.DomainModule):

    def __init__(self, loggingDirPath):

        # Hold the history of some inputs
        self.history = dict()
        self.history['last_total_rebuf'] = 0
        # Default initial bitrate index
        self.history['last_bit_rate'] = 0

        super().__init__(loggingDirPath, actionFields={'bitRate':[0,1,2,3,4,5]})

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

        return reward


if __name__ == '__main__':

    # Parse the default args
    port, address, mode, learnerDir, loggingPath, miscArgs = agents.framework_AgentServer.ParseDefaultServerArgs()

    # Setup domain definition
    domainDF = ABRControllerExperimentModule(learnerDir + loggingPath)

    # Declare a server
    server = agents.framework_AgentServer.AgentServer(domainDF, BufferBasedDecisionLogic(), (address, port))

    server.Run()