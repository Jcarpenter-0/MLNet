
if __name__ == '__main__':
    import os
    import sys
    sys.path.insert(0, os.getcwd())
    sys.path.insert(0, '../../')

import math
import learners
import learners.learnerServer


class CongestionControlExperimentProblemModule(learners.DomainModule):

    def __init__(self, loggingDirPath, traceFilePostFix=''):
        """Domain module that ONLY logs data coming into it"""
        super().__init__(loggingDirPath, traceFilePostFix=traceFilePostFix)

    def DefineReward(self, observation, rawObservation):
        return 0


if __name__ == '__main__':

    # Parse the default args
    port, address, mode, learnerDir, filePostFix, miscArgs = learners.learnerServer.ParseDefaultServerArgs()

    # Setup domain definition
    domainDF = CongestionControlExperimentProblemModule(learnerDir + 'logging_only/', traceFilePostFix=filePostFix)

    mlModule = learners.PatternModule()

    # Declare a server
    server = learners.learnerServer.MLServer(domainDF, mlModule, (address, port))

    server.Run()