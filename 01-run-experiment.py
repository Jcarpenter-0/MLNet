import os
import glob
import subprocess
import time
import shutil
import json
import sys
from datetime import datetime

import Learners.Demo.demoRL
import Network.Demo.demoNetwork
import Server.Demo.demoServer
import Client.Demo.demoClient

# Duration to run the system, is the number of training sessions or testing
# ========================================
DURATION = 1000

Server = Server.Demo.demoServer.server()

Client = Client.Demo.demoClient.client()

Network = Network.Demo.demoNetwork.network()

# Execution order (Who runs in what order and/by whom), ommissions expect someone else to start them
RunOrder = [Server, Network]

MachineLearner = Learners.Demo.demoRL.ReinforcementLearner(Server, Client, Network, './tmp/model', training=True)

# ========================================

# Reassignment of finished variables
Server.Client = Client
Server.Network = Network
Client.Network = Network
Client.Server = Server
Network.Server = Server
Network.Client = Client

try:

    for step in range(0, DURATION):

        print('Iteration:{}/{}'.format(step,DURATION))

        Server.setup()
        Client.setup()
        Network.setup()

        # Run Components
        for component in RunOrder:
            component.run()

        # client code will determine when the overall test proceeds to completion
        Client.shutdown()
        Server.shutdown()
        Network.shutdown()

        # collect the logs, edit and report them
        clientLogJson = Client.log()
        serverLogJson = Server.log()
        networkLogJson = Network.log()

        MachineLearner.Act(clientLogJson, serverLogJson, networkLogJson)

except Exception as ex:
    print(ex)
    Client.shutdown()
    Server.shutdown()
    Network.shutdown()

# output final training report
MachineLearner.log()

Client.report()
Server.report()
Network.report()
MachineLearner.report()
