import requests
import json

def ConvertArgDictToArgList(argDict):
    """Convert a pythonDict of args into a list of args in Popen format"""

    argList = []

    for para in argDict.keys():
        argList.append(para)

        if argDict[para] is not None:
            argList.append(argDict[para])

    return argList

def SendToLearner(dataDict, learnerTarget, verbose=False):
    """Send a python dict of keys/values to a targeted learner host"""

    # Send to learner, and get new action
    if verbose:
        print('application sending {}'.format(dataDict))

    # Encode from dict to JSON again
    jsonData = json.dumps(dataDict)

    response = requests.post(learnerTarget, data=jsonData)

    respDict = json.loads(response.content.decode())

    if verbose:
        print('application received {}'.format(respDict))

    return respDict
