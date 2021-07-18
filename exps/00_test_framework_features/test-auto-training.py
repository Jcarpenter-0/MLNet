# =====================================
#
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


# Load in the experiment script
experimentFilePath = sys.argv[1]

experimentFP = open(experimentFilePath, 'r')

experimentConfigs:dict = json.load(experimentFP)

# Given a set of desired environment qualities (metrics, performance, etc) create a "plan" of testing

# Then, figure out the modules needed to conduct it
