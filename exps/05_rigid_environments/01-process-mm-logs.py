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

for mmFile in mmFiles:

    up = networks.mahimahi.ParseMMLogFile(mmFile, 10)

    data.append(up)

if len(data) > 0:

    CSVHeaders = ['timestamp(ms)', 'bytes', 'delay(ms)']
    CSVHeaderLine = ','.join(CSVHeaders) + '\n'

    fp = open('{}-{}-mm.csv'.format('./tmp/', configurationName), 'w')

    fp.write(CSVHeaderLine)

    for subData in data:
        for line in subData:
            fp.write(','.join(line.values()) + '\n')

    fp.flush()
    fp.close()