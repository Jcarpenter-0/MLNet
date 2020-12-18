# Simply generate a bunch of mahimahi traces files

import random

TracePath = './mahimahi-traces/'
TracefileNames = '{}-mm-trace.txt'
NumberOfFiles = range(0, 100)
LengthsOfTraceFiles = range(1, 100)
DeliveryDensities = range(0, 100)

for fileNum in NumberOfFiles:

    fileLines = []

    # Select a file time length
    lengthIdx = random.randint(0, len(LengthsOfTraceFiles)-1)

    for timeIdx in range(0, LengthsOfTraceFiles[lengthIdx]):

        # Select a density
        density = DeliveryDensities[random.randint(0, len(DeliveryDensities)-1)]

        # write that many times into the file
        for entry in range(0, density):
            fileLines.append('{}\n'.format(timeIdx))

    # Write out the trace
    traceFP = open(TracePath + TracefileNames.format(fileNum), 'w')

    traceFP.writelines(fileLines)

    traceFP.flush()
    traceFP.close()