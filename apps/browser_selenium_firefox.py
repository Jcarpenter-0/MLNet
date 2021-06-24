import subprocess

# Setup the dir
DirOffset = '../../'

import os
import sys
sys.path.insert(0, os.getcwd())
sys.path.insert(0, DirOffset)
# Hack for overcoming some dir issues

import psutil
import apps
import time
from selenium.webdriver.remote.webdriver import WebDriver
from selenium import webdriver


def PrepCall(url:str, duration:float, iperfRunTimes:int, learnerIpAddress:str, learnerPort:int) -> list:

    commands = apps.PrepWrapperCall('{}apps/browser_selenium_firefox.py'.format(DirOffset), ['~url', url, '~duration', '{}'.format(duration)], iperfRunTimes,
                                    'http://{}:{}'.format(learnerIpAddress, learnerPort))
    return commands


def __cleannup():

    procNames = ['firefox', 'geckodriver']

    for killName in procNames:
        for proc in psutil.process_iter():
            # check whether the process name matches
            if killName in proc.name():
                proc.kill()


def __run(args:dict) -> dict:

    fireFoxOptions = webdriver.FirefoxOptions()
    profile = webdriver.FirefoxProfile()

    profile.set_preference("dom.disable_beforeunload", True)

    fireFoxOptions.headless = True

    browser = webdriver.Firefox(options=fireFoxOptions, firefox_profile=profile)

    start = time.time()
    browser.get(args['~url'])
    end = time.time()

    time.sleep(args['~duration'])

    browser.quit()
    browser.close()

    __cleannup()

    # Parse the output
    result = {}

    result['pageLoadTime'] = end-start

    return result


if __name__ == '__main__':

    argDict, currentArgs, endpoint, runcount = apps.ParseDefaultArgs()

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
            __cleannup()
            raise inter
        except subprocess.CalledProcessError as ex:
            __cleannup()
        except Exception as ex1:
            __cleannup()


