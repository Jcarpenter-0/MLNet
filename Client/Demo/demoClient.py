import subprocess
import netifaces
import socket
import os

class client:

    def __init__(self):

        self.ClientSendAmount = 20

        self.Network = None
        self.Server = None

    def setup(self):
        pass

    def run(self):
        sendAmountReduction = self.ClientSendAmount - self.Network.AvailableThroughput

        sent = self.ClientSendAmount - sendAmountReduction

        self.Server.ReceiveAmount = sent

    def shutdown(self):
        pass

    def log(self):
        jsonBody = {'setup': {},
                    'logs': {'ClientRewardVariable':self.ClientSendAmount}
                    }

        return jsonBody

    # EDITABLE - Visualize/Graph/Human readable
    def report(self):
        pass