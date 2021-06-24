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


def PrepCall(url:str, duration:float, runTimes:int, learnerIpAddress:str, learnerPort:int) -> list:

    if learnerIpAddress is not None and learnerPort is not None:

        commands = apps.PrepWrapperCall('{}apps/browser_selenium_chrome/browser_selenium_chrome.py'.format(DirOffset), ['~url', url, '~duration', '{}'.format(duration)], runTimes,
                                        'http://{}:{}'.format(learnerIpAddress, learnerPort))
    else:
        commands = apps.PrepWrapperCall('{}apps/browser_selenium_chrome/browser_selenium_chrome.py'.format(DirOffset),
                                        ['~url', url, '~duration', '{}'.format(duration)], runTimes, "")

    return commands


def __run(args:dict) -> dict:

    chromeOptions = webdriver.ChromeOptions()
    chromeOptions.headless = True
    chromeOptions.add_argument('--user-data-dir=' + '/tmp/chrome_user_dir')
    chromeOptions.add_argument('--ignore-certificate-errors')
    chromeOptions.add_argument("--autoplay-policy=no-user-gesture-required")

    browser = webdriver.Chrome(executable_path='{}apps/browser_selenium_chrome/chromedriver_linux64/chromedriver'.format(DirOffset), options=chromeOptions)

    start = time.time()
    browser.get(args['~url'])
    end = time.time()

    time.sleep(args['~duration'])

    browser.quit()

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
            raise inter
        except subprocess.CalledProcessError as ex:
            pass
        except Exception as ex1:
            print(ex1)
            raise ex1


