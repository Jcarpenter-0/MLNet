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


def PrepCall(targetServerAddress:str, targetServerPort:int,
                           agentServerAddress:str=None, agentServerPort:int=None,
                           probingApproach:int=None, probingInterface:str=None, runDuration:int=None,
                           protocol:str=None, parallelTCPConnections:int=None, logFilePath:str=None) -> list:

    commands = apps.PrepGeneralWrapperCall('apps/browser_selenium_chrome/browser_selenium_chrome.py',
                                           targetServerAddress, targetServerPort, agentServerAddress, agentServerPort,
                                           probingApproach, probingInterface, runDuration, protocol, parallelTCPConnections,
                                           logFilePath)

    return commands


class SeleniumChrome(apps.App):

    def Run(self, args:dict) -> dict:

        chromeOptions = webdriver.ChromeOptions()
        chromeOptions.headless = True
        chromeOptions.add_argument('--user-data-dir=' + '/tmp/chrome_user_dir')
        chromeOptions.add_argument('--ignore-certificate-errors')
        chromeOptions.add_argument("--autoplay-policy=no-user-gesture-required")

        browser = webdriver.Chrome(executable_path='{}apps/browser_selenium_chrome/chromedriver_linux64/chromedriver'.format(DirOffset), options=chromeOptions)

        start = time.time()
        browser.get('{}:{}{}'.format(args['-target-server-address'], args['-target--server-request-port'],
                                     args['-target-server-path']))

        end = time.time()

        time.sleep(args['-run-duration-seconds'])

        browser.quit()

        # Parse the output
        result = {}

        result['pageLoadTime'] = end-start

        return result


if __name__ == '__main__':

    apps.RunApplication(SeleniumChrome())