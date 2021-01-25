DirOffset = ''
if __name__ == '__main__':
    # Setup the dir
    DirOffset = '../../'

    import os
    import sys
    sys.path.insert(0, os.getcwd())
    sys.path.insert(0, DirOffset)

import pandas as pd
import networks.mahimahi
import math

CSVHeaders = ['timestamp(ms)', 'bytes', 'delay(ms)']
CSVHeaderLine = ','.join(CSVHeaders) + '\n'


up = networks.mahimahi.ParseMMLogFile('./data/up-log', 10)

if len(up) > 0:
    fp = open('./data/up-log.csv', 'w')

    fp.write(CSVHeaderLine)

    for line in up:
        fp.write(','.join(line.values()) + '\n')

    fp.flush()
    fp.close()

down = networks.mahimahi.ParseMMLogFile('./data/down-log', 10)

if len(down) > 0:
    fp = open('./data/down-log.csv', 'w')

    fp.write(CSVHeaderLine)

    for line in up:
        fp.write(','.join(line.values()) + '\n')

    fp.flush()
    fp.close()

