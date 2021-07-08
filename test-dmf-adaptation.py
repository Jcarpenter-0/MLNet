
import agents

# Demonstrate the DMF functionality
import apps

desiredObservation = apps.DescriptiveMetricFormat("throughput", traits=['link-level'], units=['byte','second'])

tstSerial = desiredObservation.SerializeDMF()

recievedObservation = apps.DescriptiveMetricFormat(name="throughput", value=955, traits=['application-level','per-transaction'], units=['kilobyte','minute']).ToDict()

newMetric = agents.__getMetric(desiredObservation, recievedObservation)