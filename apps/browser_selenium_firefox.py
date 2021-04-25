import subprocess

# Setup the dir
DirOffset = '../../'

import os
import sys
sys.path.insert(0, os.getcwd())
sys.path.insert(0, DirOffset)
# Hack for overcoming some dir issues

import apps
import time
from selenium.webdriver.remote.webdriver import WebDriver
from selenium import webdriver


def PrepCall(url:str, duration:float, iperfRunTimes:int, learnerIpAddress:str, learnerPort:int) -> list:

    commands = apps.PrepWrapperCall('{}apps/browser_selenium_firefox.py'.format(DirOffset), ['~url', url, '~duration', '{}'.format(duration)], iperfRunTimes,
                                    'http://{}:{}'.format(learnerIpAddress, learnerPort))
    return commands


def __run(args:dict) -> dict:

    fireFoxOptions = webdriver.FirefoxOptions()
    fireFoxOptions.headless = True

    browser = webdriver.Firefox(options=fireFoxOptions)

    start = time.time()
    browser.get(args['~url'])
    end = time.time()

    time.sleep(args['~duration'])

    browser.close()

    # Parse the output
    result = {}

    result['pageLoadTime'] = end-start

    return result


if __name__ == '__main__':

    argDict, endpoint, runcount = apps.ParseDefaultArgs()

    currentArgs = argDict.copy()

    # run n times, allows the controller to "explore" the environment
    currentRunNum = 0
    while(currentRunNum < runcount):

        exception = False

        try:

            result = __run(currentArgs)

            if endpoint is not None:
                response = apps.SendToLearner(result, endpoint)

                currentArgs = apps.UpdateArgs(currentArgs, response)

            currentRunNum += 1
        except KeyboardInterrupt as inter:
            raise inter
        except subprocess.CalledProcessError as ex:
            pass
        except Exception as ex1:
            pass


