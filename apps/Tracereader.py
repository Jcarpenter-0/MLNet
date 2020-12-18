import sys
import requests
import json
import time

# Args, ML endpoint to target, tracefile to read
MLEndpointAddressIP = sys.argv[1]

TraceFilePath = sys.argv[2]

# Send to the endpoint a jsoned tracefile row
traceFileDS = open(TraceFilePath, 'r')

traceFileLines = traceFileDS.readlines()

# Parse the header of the csv file, this will form the dict keys for each json object
headerLine = traceFileLines[0].replace('\n','')

rawKeys = headerLine.split(',')

traceFileLines = traceFileLines[1:]

for line in traceFileLines:

    line = line.replace('\n','')

    # setup dict with each key
    writeDict = dict()

    rawData = line.split(',')

    for index, rawKey in enumerate(rawKeys):
        writeDict[rawKey] = rawData[index]

    # convert to json
    jsonBody = json.dumps(writeDict).encode()

    # send to the learner
    response = requests.post(MLEndpointAddressIP, data=jsonBody)

    print(response.content.decode())