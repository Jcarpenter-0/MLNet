import subprocess
import numpy as np
import json
import shutil
import time

# Setup the dir
DirOffset = '../../'

import os
import sys
sys.path.insert(0, os.getcwd())
sys.path.insert(0, DirOffset)
# Hack for overcoming some dir issues

import apps

# Basic Python Web Server with contents
# refresh rate (when to "review" contents of the server), collect server data, and then do the learner exchange


def PrepCall(webContentDir:str, serverRate:float=1000, runTimes:int=1000, learnerIpAddress:str=None, learnerPort:int=None, apacheDir:str='/var/www/html/') -> list:

    learnerTarget = ''

    args = []

    args.append('~serverDir')
    args.append(apacheDir)

    args.append('~serverRate')
    args.append(serverRate)

    args.append('~webContentDir')
    args.append(webContentDir)

    if learnerIpAddress is not None and learnerPort is not None:
        learnerTarget = 'http://{}:{}'.format(learnerIpAddress, learnerPort)

    commands = apps.PrepWrapperCall('{}apps/http_server_apache.py'.format(DirOffset), args, runTimes, learnerTarget)
    return commands


def __run(args:dict) -> dict:

    # Since Apache runs in the background "always" we will have the "run operation" be changing the contents in the server dir

    # Move contents from webContent Dir into the apache content dir

    try:
        pass
        #shutil.rmtree( args['~serverDir'])
        #print('Application : Apache Web dir {} erased'.format(args['~serverDir']))
        #shutil.copytree(args['~webContentDir'], args['~serverDir'])
        #print('Application : Apache Web dir {} copied to {}'.format(args['~webContentDir'], args['~serverDir']))
    except Exception as ex:
        print('Application : Apache HTTP Server: Problem copying Dirs {}'.format(ex))

    time.sleep(float(args['~serverRate']))

    output = dict()

    # Add the action args
    output.update(args)

    return output


if __name__ == '__main__':

    argDict, endpoint, runcount = apps.ParseDefaultArgs()

    currentArgs = argDict.copy()

    # run n times, allows the controller to "explore" the environment
    currentRunNum = 0
    while (currentRunNum < runcount):

        result = __run(currentArgs)

        if endpoint is not None:
            response = apps.SendToLearner(result, endpoint, verbose=True)

            currentArgs = apps.UpdateArgs(currentArgs, response)

        currentRunNum += 1
