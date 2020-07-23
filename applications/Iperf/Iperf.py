import sys
import subprocess
import json
import requests
import applications.application_common

def RunIperf(iperfArgList):
    """Run Ping command and return results in Json format"""

    command = ['iperf3']
    command.extend(iperfArgList)

    if '-J' not in command:
        command.append('-J')

    # Run Iperf with initial args
    proceResult = subprocess.check_output(command)

    # Get result, decode from JSON to a dict
    proceResult = proceResult.decode()

    return json.loads(proceResult)


# Allow call to just run iperf with initial args
if __name__ == '__main__':

    # Parse the args
    iperfArgs = sys.argv[1:-1]

    # Parse the learner target
    learnerTarget = sys.argv[-1]

    result = RunIperf(iperfArgs)

    # send data to learner
    if learnerTarget is not None:
        applications.application_common.SendToLearner(result, learnerTarget)
