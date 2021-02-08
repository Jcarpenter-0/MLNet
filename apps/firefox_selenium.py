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


# Allow call to just run iperf with initial args
if __name__ == '__main__':

    argDict, endpoint, runcount = apps.ParseDefaultArgs()

    currentArgs = argDict.copy()

    retryCount = 5
    retriesRemaining = retryCount
    retryDelay = 2

    fullFailure = False

    # run n times, allows the controller to "explore" the environment
    currentRunNum = 0
    while(currentRunNum < runcount):

        exception = False

        try:

            fireFoxOptions = webdriver.FirefoxOptions()
            fireFoxOptions.headless = True

            browser = webdriver.Firefox(options=fireFoxOptions)

            browser.get('https://www.google.com/')

            browser.close()

            result = dict()

            if endpoint is not None:
                response = apps.SendToLearner(result, endpoint)

                currentArgs = apps.UpdateArgs(currentArgs, response)

            # Refresh retries
            retriesRemaining = retryCount

            currentRunNum += 1
        except KeyboardInterrupt as inter:
            raise inter
        except subprocess.CalledProcessError as ex:
            exception = True
            print(ex)
            print(ex.output)
            print(ex.returncode)

        except Exception as ex1:
            exception = True
            fullFailure = True
            print(ex1)
        finally:

            if exception and not fullFailure:

                time.sleep(retryDelay)

                if retriesRemaining > 0:
                    print('Retrying')
                    retriesRemaining = retriesRemaining - 1
                else:
                    print('Failure')
                    currentRunNum = runcount
                    raise Exception('Ran out of retries')
            elif fullFailure:
                raise Exception('Closed')

