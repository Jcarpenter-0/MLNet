if __name__ == '__main__':
    # Setup the dir
    DirOffset = '../../'

    import os
    import sys
    sys.path.insert(0, os.getcwd())
    sys.path.insert(0, DirOffset)

import glob
import networks.mahimahi

configurationName = sys.argv[1]

mmFiles = glob.glob('./tmp/{}-*'.format(configurationName))

data = []

macroData = []


for idx, mmFile in enumerate(mmFiles):

    up = networks.mahimahi.ParseMMLogFile(mmFile, 10)

    macro = networks.mahimahi.ParseMacroMMLogFileToData(mmFile, 10)

    data.append(up.append(idx))

if len(data) > 0:

    CSVHeaders = ['testRunID', 'timestamp(ms)', 'bytes', 'delay(ms)']
    CSVHeaderLine = ','.join(CSVHeaders) + '\n'

    fp = open('{}agg-{}-mm.csv'.format('./tmp/', configurationName), 'w')

    fp.write(CSVHeaderLine)

    for subData in data:
        for line in subData:
            fp.write(','.join(line.values()) + '\n')

    fp.flush()
    fp.close()