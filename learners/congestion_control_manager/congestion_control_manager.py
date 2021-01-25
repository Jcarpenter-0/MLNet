import os
import sys
sys.path.insert(0, os.getcwd())
sys.path.insert(0, '../../')

import math

import learners
import learners.learnerServer
import learners.kerasMLs


class CongestionControlExperimentProblemModule(learners.DomainModule):

    def __init__(self, loggingDirPath, traceFilePostFix=''):

        actionSpace = []

        actionSpace.append({'-Z': 'cubic'})
        actionSpace.append({'-Z': 'bbr'})
        actionSpace.append({'-Z': 'vegas'})
        actionSpace.append({'-Z': 'reno'})

        super().__init__(loggingDirPath
                         , traceFilePostFix=traceFilePostFix
                         , observationFields=[
                                'transferred_bytes',
                                'bits_per_second'
                                ]
                         , actions={
                                'cubic': [0,1],
                                'bbr': [0,1],
                                'vegas': [0,1],
                                'reno': [0,1]}
                         , actionSpace=actionSpace)

    def DefineReward(self, observation, rawObservation):
        # Copa style reward = log(throughput) - log(delay)/2 - log(lost packets)

        # Park runs at 10ms, we can try to heuristically adjust it here
        #grainAdjustment = 1000

        # goodput (stated in copa paper, backed by ccp code, backed by park code)
        throughput = float(observation['bits_per_second'])

        delay = 0

        # delay in ms (iperf gives it in usecs, backed in park, and backed in ccp codes)
        #delay = ((float(observation['meanRTT']) - float(observation['minRTT']))/1000)

        lostPackets = 0

        # TCP retransmits seem too low for it to make sense
        #lostPackets = int(rawObservation['sender-retransmits'])

        # TCP retransmits
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
    port, address, mode, learnerDir, filePostFix, miscArgs = learners.learnerServer.ParseDefaultServerArgs()

    # Setup domain definition
    domainDF = CongestionControlExperimentProblemModule(learnerDir + 'learner/', traceFilePostFix=filePostFix)

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