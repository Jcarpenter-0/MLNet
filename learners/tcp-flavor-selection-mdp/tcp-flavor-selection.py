import os
import sys
sys.path.insert(0, os.getcwd())
sys.path.insert(0, '../../')

import math

import learners
import learners.learnerServer
import learners.kerasMLs
import mdp as mdplib


class CongestionControlExperimentProblemModule(learners.MDPModule):

    def __init__(self, loggingDirPath, traceFilePostFix):

        actionSpace = []

        actionSpace.append({'-C': 'cubic'})
        actionSpace.append({'-C': 'bbr'})
        actionSpace.append({'-C': 'vegas'})
        actionSpace.append({'-C': 'reno'})
        actionSpace.append({'-C': 'bic'})
        actionSpace.append({'-C': 'htcp'})
        actionSpace.append({'-C': 'illinois'})
        actionSpace.append({'-C': 'lp'})
        actionSpace.append({'-C': 'veno'})
        actionSpace.append({'-C': 'westwood'})

        # Defining the MDP
        mdp = []

        # "lower" performance state 0
        mdp.append(mdplib.State([lambda a: self.DefineReward(a, a) <= 16.5], [0,1]))

        # "ambiguous" performance state 1
        mdp.append(mdplib.State([lambda a: self.DefineReward(a, a) > 16.5 and self.DefineReward(a, a) <= 19], [0, 1, 2]))

        # "high end" performance state 2
        mdp.append(mdplib.State([lambda a: self.DefineReward(a, a) > 19], [2]))

        super().__init__(loggingDirPath, mdp, traceFilePostFix, observationFields=['sender-bps',
                                'num_streams',
                                'blksize',
                                'duration',
                                'bytes',
                                'reverse',
                                'tcp_mss_default',
                                'meanRTT',
                                'minRTT',
                                'sender-retransmits'], actions={
                                'cubic': [0,1],
                                'bbr': [0,1],
                                'vegas': [0,1],
                                'bic': [0, 1],
                                'htcp': [0, 1],
                                'illinois': [0, 1],
                                'lp': [0, 1],
                                'veno': [0, 1],
                                'westwood': [0, 1],
                                'reno': [0,1]}, actionSpace=actionSpace)

    def DefineReward(self, observation, rawObservation):

        # Copa style reward = log(throughput) - log(delay)/2 - log(lost packets)

        # goodput (stated in copa paper, backed by ccp code, backed by park code)
        throughput = float(observation['sender-bps'])

        # delay in ms (iperf gives it in usecs, backed in park, and backed in ccp codes)
        delay = ((float(observation['meanRTT']) - float(observation['minRTT']))/1000)

        # TCP retransmits seem too low for it to make sense
        lostPackets = int(rawObservation['sender-retransmits'])

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

        # +1 input field, to count the state ID
        mlModule = learners.kerasMLs.kerasActorCritic(learnerDir, len(domainDF.ObservationFields) + 1, len(domainDF.ActionSpace))
    else:
        # pattern mode, for verification
        pattern = learners.learnerServer.loadPatternFile(miscArgs[0])

        mlModule = learners.PatternModule(pattern)

    # Declare a server
    server = learners.learnerServer.MLServer(domainDF, mlModule, (address, port))

    server.Run()