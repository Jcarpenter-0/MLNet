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


def PrepCall(targetServerAddress:str, targetServerPort:int,
                           agentServerAddress:str=None, agentServerPort:int=None,
                           probingApproach:int=None, probingInterface:str=None, runDuration:int=None,
                           protocol:str=None, parallelTCPConnections:int=None, logFilePath:str=None) -> list:

    commands = apps.PrepGeneralWrapperCall('apps/browser_selenium_firefox/browser_selenium_firefox.py',
                                           targetServerAddress, targetServerPort, agentServerAddress, agentServerPort,
                                           probingApproach, probingInterface, runDuration, protocol, parallelTCPConnections,
                                           logFilePath)

    return commands


class SeleniumFirefox(apps.App):

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

        if True:
            # Disable cache
            profile.set_preference('browser.cache.disk.enable', False)
            profile.set_preference('browser.cache.memory.enable', False)
            profile.set_preference('browser.cache.offline.enable', False)
            profile.set_preference('network.cookie.cookieBehavior', 2)

        fireFoxOptions.headless = True

        browser = webdriver.Firefox(options=fireFoxOptions, firefox_profile=profile)

        start = time.time()
        browser.get('http://{}:{}/{}'.format(args['-target-server-address'], args['-target-server-request-port'],
                                     args['-target-server-path']))
        end = time.time()

        time.sleep(args['-run-duration-seconds'])

        browser.quit()
        browser.close()

        self.__cleannup()

        # page load time
        duration = apps.framework_DMF.DurationDMF(value=end-start, unit='second', traits=['page-load-time'])

        return duration.ToDict()


if __name__ == '__main__':

    apps.RunApplication(SeleniumFirefox())


