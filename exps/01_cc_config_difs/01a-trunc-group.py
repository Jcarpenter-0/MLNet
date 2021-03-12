import glob
import pandas as pd
import sys

# Load the data in

# Truncate 11 seconds and limit to 350 seconds
truncAmountLower = 11000
truncAmountUpper = 25000

truncDataPath = sys.argv[1]
outputPath = sys.argv[2]

dataName = truncDataPath.split('/')[-1].split('.')[-2]

dataSet = pd.read_csv(truncDataPath)

# truncate
dataSet = dataSet[(dataSet['timestamp(ms)'] > truncAmountLower) & (dataSet['timestamp(ms)'] <= truncAmountUpper)]

dataSet.to_csv('{}'.format(outputPath), index=False)

print('Done')