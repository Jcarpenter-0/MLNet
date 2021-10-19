import subprocess

# Setup the dir
DirOffset = '../../'

import os
import sys
sys.path.insert(0, os.getcwd())
sys.path.insert(0, DirOffset)
# Hack for overcoming some dir issues

import psutil
import apps.framework_DMF
import time
from selenium.webdriver.remote.webdriver import WebDriver
from selenium import webdriver


def PrepCall(targetServerAddress:str, targetServerPort:int,
                           agentServerAddress:str=None, agentServerPort:int=None,
                           probingApproach:int=None, probingInterface:str=None, runDuration:int=None,
                           protocol:str=None, parallelTCPConnections:int=None, logFilePath:str=None, browser:str=None) -> list:

    commands = apps.PrepGeneralWrapperCall('apps/browser_selenium.py',
                                           targetServerAddress, targetServerPort, agentServerAddress, agentServerPort,
                                           probingApproach, probingInterface, runDuration, protocol, parallelTCPConnections,
                                           logFilePath, additionalArgs={"browser":browser})

    return commands


class SeleniumBrowser(apps.App):

    def TranslateActions(self, args:dict) -> (dict, list):
        """"""



        return ()

    def __cleannup(self):

        procNames = ['firefox', 'geckodriver']

        for killName in procNames:
            for proc in psutil.process_iter():
                # check whether the process name matches
                if killName in proc.name():
                    proc.kill()


    def Run(self, args:dict) -> dict:

        fireFoxOptions = webdriver.FirefoxOptions()
        profile = webdriver.FirefoxProfile()

        profile.set_preference("dom.disable_beforeunload", True)

        fireFoxOptions.headless = True

        browser = webdriver.Firefox(options=fireFoxOptions, firefox_profile=profile)

        start = time.time()
        browser.get('{}:{}{}'.format(args['-target-server-address'], args['-target--server-request-port'], args['-target-server-path']))
        end = time.time()

        time.sleep(args['-run-duration-seconds'])

        browser.quit()
        browser.close()

        self.__cleannup()

        # page load time
        duration = apps.framework_DMF.DurationDMF(value=end-start, unit='second', traits=['page-load-time'])

        return duration.ToDict()


if __name__ == '__main__':

    apps.RunApplication(SeleniumBrowser())


