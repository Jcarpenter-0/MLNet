import subprocess
import netifaces
import socket
import os

class client:

    def __init__(self, network, server):

        self.Network = network
        self.Server = server

    def setup(self):
        pass

    def run(self):
        pass

    def shutdown(self):
        pass

    def log(self):
        jsonBody = {'setup': {},
                    'logs': {}
                    }

        return jsonBody

    # EDITABLE - Visualize/Graph/Human readable
    def report(self):
        pass