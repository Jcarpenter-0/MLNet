# =====================================
# Demonstrate the auto-training feature.
# =====================================


import sys
import os
import glob
import json

# Setup the dir
DirOffset = '../../'

import os
import sys

sys.path.insert(0, os.getcwd())
sys.path.insert(0, DirOffset)

import exps.auto

# Load in the experiment script
experimentFilePath = './test-auto-training-example.json'

experimentFP = open(experimentFilePath, 'r')
experimentConfigs:dict = json.load(experimentFP)
experimentFP.close()

# Given a set of desired environment qualities (metrics, performance, etc) create a "plan" of testing
plannedModules, matchDegree, unresolvedDesires, warnings = exps.auto.SetupTestPlan(experimentConfigs)

print('Test Plan: {} - Desire Match: {} - Unresolved: {}'.format(plannedModules, matchDegree, unresolvedDesires, warnings))

