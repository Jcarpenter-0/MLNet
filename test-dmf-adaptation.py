
import agents

# Demonstrate the DMF functionality
import apps

desiredObservation = apps.DescriptiveMetricFormat(name="throughput", traits=['link-level'], unit='bytes-per-second')

recievedObservation = [apps.DescriptiveMetricFormat(name="transferred data", value=955, traits=['application-level','per-transaction'], unit='byte'),
                       apps.DescriptiveMetricFormat(name="duration", value=10,
                                                    traits=['application-level', 'per-transaction'], unit='second')

                       ]

newMetric = agents.__resolveDMFConversion(desiredObservation, recievedObservation)

print()