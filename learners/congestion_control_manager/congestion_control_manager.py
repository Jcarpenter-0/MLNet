import os
import sys
sys.path.insert(0, os.getcwd())
sys.path.insert(0, '../../')

import math

import learners.common
import learners.preBuiltLearners
import learners.kerasMLs


class CongestionControlExperimentProblemModule(learners.common.DomainModule):

    def __init__(self, loggingDirPath, traceFilePostFix=''):

        actionSpace = []

        actionSpace.append({'-C': 'cubic'})
        actionSpace.append({'-C': 'bbr'})
        actionSpace.append({'-C': 'vegas'})
        actionSpace.append({'-C': 'reno'})

        super().__init__(loggingDirPath
                         , traceFilePostFix=traceFilePostFix
                         , observationFields=[
                                    'receiver-bps'
                                , 'sender-retransmits'
                                , 'num_streams'
                                , 'timesecs'
                                , 'blksize'
                                , 'duration'
                                , 'tcp_mss_default'
                                , 'maxRTT'
                                , 'minRTT'
                                , 'meanRTT'
                                , 'max_snd_cwnd'
                                , 'avg_snd_cwnd'
                                , 'min_snd_cwnd'
                                ]
                         , actions={
                                'cubic': [0,1],
                                'bbr': [0,1],
                                'vegas': [0,1],
                                'reno': [0,1]}
                         , actionSpace=actionSpace)


    def DefineReward(self, observation):
        # Copa style reward = log(throughput) - log(delay)/2 - log(lost packets)

        throughput = float(observation['receiver-bps'])
        delay = float(observation['meanRTT']) - float(observation['minRTT'])
        lostPackets = float(observation['sender-retransmits'])

        reward = 0

        if throughput > 0:
            reward = math.log2(throughput)

        if delay > 0:
            reward = reward - (math.log2(delay) * 0.5)

        if lostPackets > 0:
            reward = reward - math.log2(lostPackets)

        return reward


if __name__ == '__main__':

    # Parse the default args
    port, address, mode, learnerDir, filePostFix, miscArgs = learners.common.ParseDefaultServerArgs()

    # Setup domain definition
    domainDF = CongestionControlExperimentProblemModule(learnerDir + 'learner/', traceFilePostFix=filePostFix)

    # Depending on mode
    if mode == 1 or mode == 0:
        # training/testing
        mlModule = learners.kerasMLs.kerasActorCritic(learnerDir, len(domainDF.ObservationFields), len(domainDF.ActionSpace))

    else:
        # pattern mode, for verification

        # pattern
        pattern = learners.loadPatternFile(miscArgs[0])

        mlModule = learners.common.PatternModule(pattern)

    # Declare a server
    server = learners.common.MLServer(domainDF, mlModule, (address, port))

    try:
        server.serve_forever()
    except:
        pass
    finally:
        server.Cleanup()