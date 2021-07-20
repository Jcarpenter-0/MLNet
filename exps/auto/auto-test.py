# Setup the dir
DirOffset = '../../'

import os
import sys

sys.path.insert(0, os.getcwd())
sys.path.insert(0, DirOffset)

import json
import glob
import agents.framework_AgentServer
import exps.auto
import exps

# can be a file or directory
experimentPath = sys.argv[1]


def RunExperiment(experimentConfig:dict):
    """Run an experiment using the auto-test"""

    # Apply the "onionization"

    # Figure out the learner stuff
    learners = []

    for idx, learner in enumerate(experimentConfig['learners']):
        learners.append(agents.framework_AgentServer.AgentWrapper(learner['learner-script-path'],
                                                                  learner['learner-output-path'],
                                                                  8080+idx,
                                                                  learner['training'],
                                                                  logFileName=learner['log-file-name']))

    # Figure out the environment stuff
    networkModule = exps.auto.autoBuildEnv(learners[0], soughtMetrics=experimentConfig['sought-metrics'],
                                           networkArgs=experimentConfig['network-configs'], tags=experimentConfig['tags'])

    # Execute the test
    exps.runExperimentUsingFramework(networkModule, int(experimentConfig['test-duration-seconds']))


if os.path.isdir(experimentPath):
    # it is a directory of experiment files
    experimentFiles = glob.glob(experimentPath + '*.json')

    print('Running Experiment Group: {} x{}'.format(experimentPath, len(experimentFiles)))


elif os.path.isfile(experimentPath):
    # it is an experiment file
    expFP = open(experimentPath, 'r')

    experimentConfig = json.load(expFP)

    expFP.close()

    RunExperiment(experimentConfig)

