import os
import sys
sys.path.insert(0, os.getcwd())
sys.path.insert(0, '../../')
import learners.common
import learners.preBuiltLearners


class PingExperimentExampleDomainDefinition(learners.common.DomainDefinition):

    def __init__(self, loggingDirPath):
        """Ping experiment domain def, just a simple desire,
        lower rttAvg and packet loss by selecting size of packet payload"""
        super().__init__(loggingDirPath
                         , observationFields=['-c', '-s', '-t', 'packetLoss', 'rttAvg']
                         , actions={"-c": [10], "-s": range(56, 896, 56), "-t": [255]})

    def DefineReward(self, observation):
        """Simple reward, desire lower rttAvg and packet loss"""
        return 0 - float(observation["rttAvg"]) * 1 - float(observation["packetLoss"]) * 3


if __name__ == '__main__':

    # Parse the default args
    port, address, training, learnerDir = learners.common.ParseDefaultServerArgs()

    # Setup domain definition
    domainDF = PingExperimentExampleDomainDefinition(learnerDir + 'Traces/')

    # Setup the ML module
    obvFields = domainDF.ObservationFields

    mlModule = learners.preBuiltLearners.KerasEnsemblePredictive(learnerDir
                                                                 , ['packetLoss', 'rttAvg']
                                                                 , obvFields)

    # Declare a server
    server = learners.common.MLServer(domainDF, mlModule, (address, port))

    # Start the server
    print('Server up at http://localhost:{}'.format(port))

    try:
        server.serve_forever()
    except:
        pass
    finally:
        server.Cleanup()