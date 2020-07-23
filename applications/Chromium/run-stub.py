import sys
import time
import subprocess

# Visit a webpage n times
# Time between page loads in seconds
TestDelay = 0.3
# time to let the page sit before stopping
PageWait = 1

runCount = int(sys.argv[1])

#
webTarget = sys.argv[2]

# Get learner endpoint
learner = None
try:
    learner = sys.argv[3]
except:
    pass

for runNum in range(0, runCount):

    # goto page
    chromiumResult = subprocess.check_output(['chromium-browser', webTarget])

    # Get result, decode from JSON to a dict
    chromiumResult = chromiumResult.decode()

    time.sleep(TestDelay)

    # contact learner
