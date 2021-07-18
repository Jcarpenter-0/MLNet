import os
import sys
sys.path.insert(0, os.getcwd())
sys.path.insert(0, '../../')

import math

import agents.framework_AgentServer
import agents.kerasMLs
import apps.framework_DMF


class CongestionControlExperimentProblemModule(apps.framework_DMF.AdaptationModule):

    def __init__(self, loggingDirPath, logFileName):

        actionSpace = []

        actionSpace.append({'-tcp-congestion-control': 'cubic'})
        actionSpace.append({'-tcp-congestion-control': 'vegas'})
        actionSpace.append({'-tcp-congestion-control': 'bbr'})
        actionSpace.append({'-tcp-congestion-control': 'reno'})
        actionSpace.append({'-tcp-congestion-control': 'bic'})
        actionSpace.append({'-tcp-congestion-control': 'htcp'})
        actionSpace.append({'-tcp-congestion-control': 'illinois'})
        actionSpace.append({'-tcp-congestion-control': 'lp'})
        actionSpace.append({'-tcp-congestion-control': 'veno'})
        actionSpace.append({'-tcp-congestion-control': 'westwood'})

        desiredObservationMetrics = []

        desiredObservationMetrics.append(apps.framework_DMF.LossDMF(unit='byte'))
        desiredObservationMetrics.append(apps.framework_DMF.DurationDMF(unit='second'))
        desiredObservationMetrics.append(apps.framework_DMF.LatencyDMF(unit='millisecond'))
        desiredObservationMetrics.append(apps.framework_DMF.RoundTripTimeDMF(unit='millisecond', traits=['min']))
        desiredObservationMetrics.append(apps.framework_DMF.RoundTripTimeDMF(unit='millisecond', traits=['mean']))
        desiredObservationMetrics.append(apps.framework_DMF.ThroughputDMF(unit='byte'))
        desiredObservationMetrics.append(apps.framework_DMF.ParallelStreamsDMF(unit='tcp-stream'))
        desiredObservationMetrics.append(apps.framework_DMF.DataSentDMF(unit='byte'))

        super().__init__(logPath=loggingDirPath, logFileName=logFileName, desiredObservationMetrics=desiredObservationMetrics, actionSpace=actionSpace)

    def DefineReward(self, observation, rawObservation):
        # Copa style reward = log(throughput) - log(delay)/2 - log(lost packets)

        # goodput (stated in copa paper, backed by ccp code, backed by park code)
        throughput = float(rawObservation[self.DesiredObservations[5].GetDMFLabel()])

        # delay in ms (iperf gives it in usecs, backed in park, and backed in ccp codes)
        delay = ((float(rawObservation[self.DesiredObservations[3].GetDMFLabel()]) - float(rawObservation[self.DesiredObservations[4].GetDMFLabel()]))/1000)

        # TCP retransmits seem too low for it to make sense
        lostPackets = int(rawObservation[self.DesiredObservations[0].GetDMFLabel()])

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
    port, address, mode, learnerDir, loggingPath, logFileName, miscArgs = agents.framework_AgentServer.ParseDefaultServerArgs()

    # Setup domain definition
    domainDF = CongestionControlExperimentProblemModule(learnerDir + loggingPath, logFileName)

    # Depending on mode
    if mode == 1 or mode == 0:
        # training/testing
        mlModule = agents.kerasMLs.kerasActorCritic(learnerDir, len(domainDF.DesiredObservations), len(domainDF.ActionSpace))
    else:
        mlModule = agents.RepeatModule()

    # Declare a server
    server = agents.framework_AgentServer.AgentServer(domainDF, mlModule, (address, port))

    server.Run()