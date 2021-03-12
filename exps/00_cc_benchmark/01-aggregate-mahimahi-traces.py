DirOffset = ''
if __name__ == '__main__':
    # Setup the dir
    DirOffset = '../../'

    import os
    import sys
    sys.path.insert(0, os.getcwd())
    sys.path.insert(0, DirOffset)

import networks.mahimahi

inputfilePath = sys.argv[1]
inputFileName = inputfilePath.split('/')[-1]

outputPath = sys.argv[2]


CSVHeaders = ['timestamp(ms)', 'bytes', 'delay(ms)']
CSVHeaderLine = ','.join(CSVHeaders) + '\n'

up = networks.mahimahi.ParseMMLogFile(inputfilePath, 10)

if len(up) > 0:
    fp = open('{}{}.csv'.format(outputPath, inputFileName), 'w')

    fp.write(CSVHeaderLine)

    for line in up:
        fp.write(','.join(line.values()) + '\n')

    fp.flush()
    fp.close()
