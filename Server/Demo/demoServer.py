import os
import glob
import subprocess
import time
import json
import shutil
from datetime import datetime
import numpy as np

class server:

    def __init__(self):

        self.ReceiveAmount = 0

        self.Network = None
        self.Client = None

    def setup(self):
        pass

    def run(self):
        pass

    def shutdown(self):
        self.ReceiveAmount = 0

    def log(self):

        jsonBody = {'setup': {},
                    'logs': {'ServerRewardVariable':self.ReceiveAmount}
                    }

        return jsonBody

    # EDITABLE - Visualize/Graph/Human readable
    def report(self):

        pass