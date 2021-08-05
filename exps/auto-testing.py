# Setup the dir
DirOffset = '../../'

import os
import sys

sys.path.insert(0, os.getcwd())
sys.path.insert(0, DirOffset)

import json
import glob
import exps

# can be a file or directory
experimentPath = sys.argv[1]

if os.path.isdir(experimentPath):
    # it is a directory of experiment files
    experimentFiles = glob.glob(experimentPath + '*.json')

    print('Running Experiment Group: {} x{}'.format(experimentPath, len(experimentFiles)))

    for idx, file in enumerate(experimentFiles):
        expFP = open(file, 'r')

        experimentConfig = json.load(expFP)

        expFP.close()

        print('Test {}/{}'.format(idx+1,len(experimentFiles)))
        exps.RunExperimentPlanUsingFramework(experimentConfig)


elif os.path.isfile(experimentPath):
    # it is an experiment file
    expFP = open(experimentPath, 'r')

    experimentConfig = json.load(expFP)

    expFP.close()

    exps.RunExperimentPlanUsingFramework(experimentConfig)

