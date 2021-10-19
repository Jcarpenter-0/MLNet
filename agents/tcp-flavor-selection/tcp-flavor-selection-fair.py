import os
import sys
sys.path.insert(0, os.getcwd())
sys.path.insert(0, '../../')

import math

import agents.framework_AgentServer
import agents.kerasMLs
import apps.framework_DMF


class CongestionControlExperimentProblemModule(agents.DomainModule):

    def __init__(self, loggingDirPath, logFileName, agentCount:int=1, linkQuality:int=0):

        # for experimental checks
        self.LinkQuality = linkQuality
        self.AgentCount = agentCount

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

        super().__init__(logPath=loggingDirPath, logFileName=logFileName, actionSpace=actionSpace)

    def DefineReward(self, observation, rawObservation):

        reward, fairness = agents.CoreReward(throughputMbps=apps.framework_DMF.GetMetric('throughput', rawObservation).Value/1000/1000,
                                             timeCompletionSeconds=apps.framework_DMF.GetMetric('round-trip-time', rawObservation).Value/1000,
                                             allowedBandwidthMbps=self.LinkQuality/self.AgentCount,
                                             fairnessWeight=0.5)

        rawObservation["fairness"] = fairness
        rawObservation["allowed"] = self.LinkQuality/self.AgentCount

        return reward


if __name__ == '__main__':

    # Parse the default args
    args = agents.framework_AgentServer.ParseDefaultServerArgs()

    # Setup domain definition
    if 'agentCount' in args.keys():
        domainDF = CongestionControlExperimentProblemModule(args['AgentDir'] + args['LogPath'], args['LogFileName'], agentCount=args['agentCount'], linkQuality=args['linkQuality'])
    else:
        domainDF = CongestionControlExperimentProblemModule(args['AgentDir'] + args['LogPath'], args['LogFileName'])

    # Depending on mode
    if args['Training'] == 1 or args['Training'] == 0:
        # training/testing
        mlModule = agents.kerasMLs.kerasActorCritic(args['AgentDir'], 27, len(domainDF.ActionSpace))
    else:
        if 'actionIndex' in args.keys():
            mlModule = agents.RepeatModule(int(args['actionIndex']))
        else:
            mlModule = agents.RepeatModule()

    # Declare a server
    server = agents.framework_AgentServer.AgentServer(domainDF, mlModule, ('', args['AgentPort']))

    server.Run()