import os
import sys
sys.path.insert(0, os.getcwd())
sys.path.insert(0, '../../')

import math
import numpy as np
import learners
import learners.learnerServer
import learners.kerasMLs


# Some constants from Park and Pensieve's reward functions
M_IN_K = 1000.0
VIDEO_BIT_RATE = [300,750,1200,1850,2850,4300]  # Kbps


class ABRControllerExperimentModule(learners.DomainModule):

    def __init__(self, loggingDirPath, traceFilePostFix=''):

        # Hold the history of some inputs
        self.history = dict()
        self.history['last_total_rebuf'] = 0
        # Default initial bitrate index
        self.history['last_bit_rate'] = 0

        super().__init__(loggingDirPath
                         , traceFilePostFix=traceFilePostFix
                         , observationFields=[]
                         , actions={'bitrate':[0,1,2,3,4,5]})

    def DefineReward(self, observation, rawObservation):
        """Reward function as outlined by Park and Pensieve: --linear reward-- """
        SMOOTH_PENALTY = 1
        REBUF_PENALTY = 4.3  # 1 sec rebuffering -> this number of Mbps

        rebuffer_time = float(rawObservation['RebufferTime'] - self.history['last_total_rebuf'])

        reward = VIDEO_BIT_RATE[rawObservation['lastquality']] / M_IN_K - REBUF_PENALTY * rebuffer_time / M_IN_K - SMOOTH_PENALTY * np.abs(VIDEO_BIT_RATE[rawObservation['lastquality']] - self.history['last_bit_rate']) / M_IN_K

        self.history['last_bit_rate'] = VIDEO_BIT_RATE[rawObservation['lastquality']]
        self.history['last_total_rebuf'] = rawObservation['RebufferTime']

        return reward


if __name__ == '__main__':

    # Parse the default args
    port, address, mode, learnerDir, filePostFix, miscArgs = learners.learnerServer.ParseDefaultServerArgs()

    # Setup domain definition
    domainDF = ABRControllerExperimentModule(learnerDir + 'learner/', traceFilePostFix=filePostFix)

    # Depending on mode
    if mode == 1 or mode == 0:
        # training/testing
        mlModule = learners.kerasMLs.kerasActorCritic(learnerDir, len(domainDF.ObservationFields), len(domainDF.ActionSpace))
    else:
        # pattern mode, for verification
        pattern = learners.learnerServer.loadPatternFile(miscArgs[0])

        mlModule = learners.PatternModule(pattern)

    # Declare a server
    server = learners.learnerServer.MLServer(domainDF, mlModule, (address, port))

    server.Run()