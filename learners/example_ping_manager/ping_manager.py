import os
import sys
sys.path.insert(0, os.getcwd())
sys.path.insert(0, '../../')

import learners.kerasMLs
import learners
import learners.preBuiltLearners


class PingExperimentExampleDomainModule(learners.DomainModule):

    def __init__(self, loggingDirPath, traceFilePostFix=''):
        """Ping experiment domain def, just a simple desire,
        lower rttAvg and packet loss by selecting size of packet payload"""
        super().__init__(loggingDirPath
                         , traceFilePostFix=traceFilePostFix
                         , observationFields=['packetLoss', 'rttAvg']
                         , actions={"-c": [10], "-s": [56, 32753, 65507], "-t": [255]})
        self.PreviousPacketLoss = 0.0
        self.PreviousRTTavg = 0.0

    def DefineObservation(self, observation):

        # Record the previous RTT and Loss
        observation['prev-packetLoss'] = self.PreviousPacketLoss
        observation['prev-rttAvg'] = self.PreviousRTTavg

        self.PreviousPacketLoss = observation['packetLoss']
        self.PreviousRTTavg = observation['rttAvg']

        obv = super(PingExperimentExampleDomainModule, self).DefineObservation(observation)

        return obv

    def DefineReward(self, observation):
        """Simple reward, desire lower rttAvg and packet loss"""
        return 0 - float(observation["rttAvg"]) * 1 - float(observation["packetLoss"]) * 3


if __name__ == '__main__':

    # Parse the default args
    port, address, training, learnerDir, traceFilePost, miscArgs = learners.ParseDefaultServerArgs()

    # Setup domain definition
    domainDF = PingExperimentExampleDomainModule(learnerDir, traceFilePostFix=traceFilePost)

    # Setup the ML module
    obvFields = domainDF.ObservationFields

    if training != 2:

        mlModule = learners.kerasMLs.kerasActorCritic(learnerDir, len(obvFields), len(domainDF.ActionSpace))

    else:
        # Load the pattern
        pattern = learners.loadPatternFile(miscArgs[0])

        mlModule = learners.PatternModule(pattern)


    # Declare a server
    server = learners.MLServer(domainDF, mlModule, (address, port))

    # Start the server
    print('Server up at http://localhost:{}'.format(port))

    try:
        server.serve_forever()
    except:
        pass
    finally:
        server.Cleanup()