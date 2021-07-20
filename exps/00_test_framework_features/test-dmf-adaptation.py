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

# Case 0, no such metric
# What do you want?
desiredObservation = [apps.framework_DMF.DurationDMF(unit='nonsecond', value=2039, traits=['per-transaction'])]

# What do you have?
recievedObservation = {}
recievedObservation.update(apps.framework_DMF.DurationDMF(unit='second', value=10, traits=['application-level', 'per-transaction']).ToDict())

# What resulted
newMetrics = apps.framework_DMF._getMetrics(desiredObservation, recievedObservation)

print('-------------------------------')
for metric in newMetrics:
    print('{}'.format(metric.__dict__))




# Case 1, just a conversion of units

# What do you want?
desiredObservation = [apps.framework_DMF.DurationDMF(unit='millisecond', traits=['per-transaction'])]

# What do you have?
recievedObservation = {}
recievedObservation.update(apps.framework_DMF.DurationDMF(unit='second', value=10, traits=['application-level', 'per-transaction']).ToDict())

# What resulted
newMetrics = apps.framework_DMF._getMetrics(desiredObservation, recievedObservation)

print('Case 1 ------------------------')
for metric in newMetrics:
    print('{}'.format(metric.__dict__))

# Case 2, create new metric

# What do you want?
desiredObservation = [apps.framework_DMF.ThroughputDMF(unit='bytes-per-second', traits=['per-transaction'])]

# What do you have?
recievedObservation = {}
recievedObservation.update(apps.framework_DMF.DataReceivedDMF(unit='byte', value=955, traits=['application-level']).ToDict())
recievedObservation.update(apps.framework_DMF.DataReceivedDMF(unit='byte', value=915, traits=['per-transaction']).ToDict())
recievedObservation.update(apps.framework_DMF.DurationDMF(unit='second', value=10, traits=['application-level', 'per-transaction']).ToDict())

# What resulted
newMetrics = apps.framework_DMF._getMetrics(desiredObservation, recievedObservation)

print('-------------------------------')
for metric in newMetrics:
    print('{}'.format(metric.__dict__))

