import glob
import pandas as pd
import sys

# Load the data in
outputPath = sys.argv[1]
combinatorialData = sys.argv[2:]

dataFrames = list()
dataCols = list()

for combData in combinatorialData:

    dataName = combData.split('/')[-1].split('.')[-2]

    dataSet = pd.read_csv(combData)

    dataFrames.append(dataSet)

    dataCols.append(dataName)


outputDF = pd.concat(dataFrames, axis=1, keys=dataCols, ignore_index=True)

outputDF[dataCols[0]] = outputDF[0]
outputDF[dataCols[1]] = outputDF[1]

outputDF = outputDF.drop(columns=[0,1])

outputDF.to_csv(outputPath, index=False)

print('Done')