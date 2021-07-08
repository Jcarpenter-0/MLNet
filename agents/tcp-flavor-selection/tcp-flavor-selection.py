import os
import sys
sys.path.insert(0, os.getcwd())
sys.path.insert(0, '../../')

import math

import agents.agentServer
import agents.kerasMLs


class CongestionControlExperimentProblemModule(agents.DomainModule):

    def __init__(self, loggingDirPath):

        actionSpace = []

        actionSpace.append({'-C': 'vegas'})
        actionSpace.append({'-C': 'cubic'})
        actionSpace.append({'-C': 'bbr'})
        actionSpace.append({'-C': 'reno'})
        actionSpace.append({'-C': 'bic'})
        actionSpace.append({'-C': 'htcp'})
        actionSpace.append({'-C': 'illinois'})
        actionSpace.append({'-C': 'lp'})
        actionSpace.append({'-C': 'veno'})
        actionSpace.append({'-C': 'westwood'})

        super().__init__(loggingDirPath, actionSpace=actionSpace)

    def DefineObservation(self, rawObservation:dict) -> list:

        desiredFields = ['sender-bps'
            ,'num_streams'
            ,'blksize'
            ,'duration'
            ,'bytes'
            ,'reverse'
            ,'tcp_mss_default'
            ,'meanRTT'
            ,'minRTT'
            ,'sender-retransmits']

        observation = []

        for value in desiredFields:
            observation.append(rawObservation[value])

        return observation

    def DefineReward(self, observation, rawObservation):
        # Copa style reward = log(throughput) - log(delay)/2 - log(lost packets)

        # goodput (stated in copa paper, backed by ccp code, backed by park code)
        throughput = float(rawObservation['sender-bps'])

        # delay in ms (iperf gives it in usecs, backed in park, and backed in ccp codes)
        delay = ((float(rawObservation['meanRTT']) - float(rawObservation['minRTT']))/1000)

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
    port, address, mode, learnerDir, loggingPath, miscArgs = agents.agentServer.ParseDefaultServerArgs()

    # Setup domain definition
    domainDF = CongestionControlExperimentProblemModule(learnerDir + loggingPath)

    # Depending on mode
    if mode == 1 or mode == 0:
        # training/testing
        mlModule = agents.kerasMLs.kerasActorCritic(learnerDir, 10, len(domainDF.ActionSpace))
    else:
        mlModule = agents.RepeatModule()

    # Declare a server
    server = agents.agentServer.AgentServer(domainDF, mlModule, (address, port))

    server.Run()