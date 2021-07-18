# =====================================
# Test and demonstrate the DMF adaptation system
# =====================================


# Setup the dir
DirOffset = '../../'

import os
import sys

sys.path.insert(0, os.getcwd())
sys.path.insert(0, DirOffset)

# Demonstrate the DMF functionality
import apps.framework_DMF

# What do you want?
desiredObservation = [apps.ThroughputDMF(unit='bytes-per-second', traits=['per-transaction'])]


# What do you have?
recievedObservation = {}

recievedObservation.update(apps.DataReceivedDMF(unit='byte', value=955, traits=['application-level']).ToDict())
recievedObservation.update(apps.DataReceivedDMF(unit='byte', value=915, traits=['application-level','per-transaction']).ToDict())
recievedObservation.update(apps.DurationDMF(unit='second', value=10, traits=['application-level', 'per-transaction']).ToDict())


# What resulted
newMetrics = apps.framework_DMF._getMetrics(desiredObservation, recievedObservation)

for metric in newMetrics:
    print('{}'.format(metric.ToDict()))