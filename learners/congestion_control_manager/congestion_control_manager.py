import os
import sys
sys.path.insert(0, os.getcwd())
sys.path.insert(0, '../../')
import learners.common
import learners.preBuiltLearners


class CongestionControlExperimentProblemModule(learners.common.DomainModule):

    def __init__(self, loggingDirPath, traceFilePostFix=''):
        super().__init__(loggingDirPath
                         , traceFilePostFix=traceFilePostFix
                         , observationFields=[
                'bps-0'
            , 'retransmits-0'
            , 'cubic'
            , 'bbr'
            , 'vegas'
            , 'reno'
            , 'bps-1'
            , 'retransmits-1']
                         , actions={
                'cubic': range(0, 2),
                'bbr': range(0, 2),
                'vegas': range(0, 2),
                'reno': range(0, 2)})

    def DefineActionSpaceSubset(self):

        actions = []

        actions.append({'cubic': 1, 'bbr': 0, 'vegas': 0, 'reno': 0})
        actions.append({'cubic': 0, 'bbr': 1, 'vegas': 0, 'reno': 0})
        actions.append({'cubic': 0, 'bbr': 0, 'vegas': 1, 'reno': 0})
        actions.append({'cubic': 0, 'bbr': 0, 'vegas': 0, 'reno': 1})

        return actions

    def DefineReward(self, observation):
        return float(observation["bps-1"]) * 2 - float(observation["retransmits-1"]) * 1


if __name__ == '__main__':

    # Parse the default args
    port, address, mode, learnerDir, filePostFix, miscArgs = learners.common.ParseDefaultServerArgs()

    # Setup domain definition
    domainDF = CongestionControlExperimentProblemModule(learnerDir + 'Traces/', traceFilePostFix=filePostFix)

    # Setup the ML module
    obvFields = domainDF.ObservationFields

    # Depending on mode
    if mode == 1 or mode == 0:
        # training/testing
        mlModule = learners.preBuiltLearners.KerasEnsemblePredictive(learnerDir
                                                                 , ['bps-1','retransmits-1']
                                                                 , obvFields
                                                                 , training=mode == 1)
    else:
        # pattern mode, for verification

        # pattern
        patternPath = miscArgs[0]

        patternFP = open(patternPath, 'r')
        patternLines = patternFP.readlines()

        # Load the header
        patternHeader = patternLines[0].split(',')

        pattern = list()

        for line in patternLines[1:]:

            lineDict = dict()

            linePieces = line.split(',')

            for col in patternHeader:
                lineDict[col] = linePieces

            pattern.append(lineDict)

        mlModule = learners.common.PatternModule(pattern)

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