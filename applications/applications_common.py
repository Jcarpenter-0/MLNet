import http.server
import sys
import subprocess
import os
import time

# Harness for running Applications

class OperationServerHandler(http.server.SimpleHTTPRequestHandler):

    # Recieve Action from Learner
    def do_POST(self):

        # Parse out necessary parameters

        # Send to the application/begin new application step

        # Finish web transaction

        return NotImplementedError

class OperationServer(object):
    def __init__(self, learnerAddresses):
        self.serverAddress = ('', 8000)
        self.httpd = http.server.HTTPServer(self.serverAddress, OperationServerHandler)
        self.Command = ''
        self.LearningSendPoints = learnerAddresses

    def run(self):
        self.httpd.serve_forever()

    def cleanup(self):
        self.httpd.shutdown()