import os
import sys
sys.path.insert(0, os.getcwd())
sys.path.insert(0, '../../')

import math

import learners
import learners.learnerServer
import learners.kerasMLs


class CongestionControlExperimentProblemModule(learners.DomainModule):

    def __init__(self, loggingDirPath, traceFilePostFix='', actionSpace=[], observationFields=[]):

        super().__init__(loggingDirPath
                         , traceFilePostFix=traceFilePostFix
                         , observationFields=observationFields
                         , actions={
                                'cubic': [0,1],
                                'bbr': [0,1],
                                'vegas': [0,1],
                                'bic': [0, 1],
                                'htcp': [0, 1],
                                'illinois': [0, 1],
                                'lp': [0, 1],
                                'veno': [0, 1],
                                'westwood': [0, 1],
                                'reno': [0,1]}
                         , actionSpace=actionSpace)

    def DefineReward(self, observation, rawObservation):

        if 'receiver-bps' in observation:
            throughput = float(observation['receiver-bps'])
        else:
            throughput = float(observation['bits_per_second'])

        # TCP retransmits
        reward = 0

        if throughput > 0:
            reward = math.log2(throughput)

        return reward


if __name__ == '__main__':

    # Parse the default args
    port, address, mode, learnerDir, filePostFix, miscArgs = learners.learnerServer.ParseDefaultServerArgs()

    # Setup domain definition
    if int(miscArgs[1]) == 1:
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

        domainDF = CongestionControlExperimentProblemModule(learnerDir + 'learner/', traceFilePostFix=filePostFix, actionSpace=actionSpace, observationFields=['receiver-bps', 'receiver-bytes'])
    else:
        actionSpace = []

        actionSpace.append({'-Z': 'cubic'})
        actionSpace.append({'-Z': 'bbr'})
        actionSpace.append({'-Z': 'vegas'})
        actionSpace.append({'-Z': 'reno'})
        actionSpace.append({'-Z': 'bic'})
        actionSpace.append({'-Z': 'htcp'})
        actionSpace.append({'-Z': 'illinois'})
        actionSpace.append({'-Z': 'lp'})
        actionSpace.append({'-Z': 'veno'})
        actionSpace.append({'-Z': 'westwood'})

        domainDF = CongestionControlExperimentProblemModule(learnerDir + 'learner/', traceFilePostFix=filePostFix, actionSpace=actionSpace, observationFields=['bits_per_second', 'transferred_bytes'])

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