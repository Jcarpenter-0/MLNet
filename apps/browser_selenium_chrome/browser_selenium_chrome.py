import subprocess

# Setup the dir
DirOffset = '../../'

import os
import sys
sys.path.insert(0, os.getcwd())
sys.path.insert(0, DirOffset)
# Hack for overcoming some dir issues

import apps
import apps.framework_DMF
import time
from selenium.webdriver.remote.webdriver import WebDriver
from webdriver_manager.chrome import ChromeDriverManager
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
        chromeOptions.headless = False
        chromeOptions.add_argument('--user-data-dir=' + '/tmp/chrome_user_dir')
        chromeOptions.add_argument('--ignore-certificate-errors')
        chromeOptions.add_argument("--autoplay-policy=no-user-gesture-required")
        chromeOptions.add_argument("--disk-cache-size=0")

        #browser = webdriver.Chrome(executable_path='{}apps/browser_selenium_chrome/chromedriver_linux64/chromedriver'.format(DirOffset), options=chromeOptions)
        browser = webdriver.Chrome(ChromeDriverManager().install(),
            options=chromeOptions)

        # Open the dev tools thing to lock the cache out
        if '-open-dev-tools' in args.keys():
            time.sleep(1)
            print('Selenium:Chrome: Opening Dev Tools')
            devToolOpener = subprocess.check_call(['xdotool', 'key', 'F12'])


        #input('Wait')

        start = time.time()
        print('http://{}:{}/{}'.format(args['-target-server-address'], args['-target-server-request-port'], args['-target-server-path']))
        browser.get('http://{}:{}/{}'.format(args['-target-server-address'], args['-target-server-request-port'],
                                     args['-target-server-path']))

        end = time.time()

        time.sleep(int(args['-run-duration-seconds']))

        browser.close()
        browser.quit()

        # Parse the output
        duration = apps.framework_DMF.DurationDMF(value=end - start, unit='second', traits=['page-load-time'])

        return duration.ToDict()


if __name__ == '__main__':

    apps.RunApplication(SeleniumChrome())