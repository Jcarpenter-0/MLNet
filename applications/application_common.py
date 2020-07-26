import requests
import json
import subprocess


class ActionModule(object):
    """Translate action IDs into command parameters"""
    def __init__(self):
        return

    """Translate an actionID into new args, return a list of the args, similar to Popen format"""
    def TranslateToAction(self, actionID):
        return NotImplementedError


def ConvertArgDictToArgList(argDict):
    """Convert a pythonDict of args into a list of args in Popen format"""

    argList = []

    for para in argDict.keys():
        argList.append(para)

        if argDict[para] is not None:
            argList.append(argDict[para])

    return argList

"""Expands the action ID into binary columns for data"""
def SetActionBinaries(actionID, totalActions, dataDict):

    for actionIndex in range(0, totalActions):

        if actionID == actionIndex:
            dataDict['actionID-{}'.format(actionIndex)] = 1
        else:
            dataDict['actionID-{}'.format(actionIndex)] = 0

    return dataDict

"""Send pythonDict as json to the post reception of a learner server"""
def SendToLearner(dataDict, learnerTarget, verbose=False):
    # Send to learner, and get new action
    if verbose:
        print('Sending {}'.format(dataDict))

    # Encode from dict to JSON again
    jsonData = json.dumps(dataDict)

    response = requests.post(learnerTarget, data=jsonData)

    respDict = json.loads(response.content.decode())

    if verbose:
        print('received {}'.format(respDict))

    return int(respDict['actionID'])

def SendToLearnerL(dataDict, learnerTarget, verbose=False):
    # Send to learner, and get new action
    if verbose:
        print('Sending {}'.format(dataDict))

    # Encode from dict to JSON again
    jsonData = json.dumps(dataDict)

    response = requests.post(learnerTarget, data=jsonData)

    respDict = json.loads(response.content.decode())

    if verbose:
        print('received {}'.format(respDict))

    return respDict
