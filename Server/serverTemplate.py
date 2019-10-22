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
        self.Network = None
        self.Client = None

    def setup(self):
        pass

    def run(self):
        pass

    def shutdown(self):
        pass

    def log(self):

        jsonBody = {'setup': {},
                    'logs': {'ClientRewardVariable':3}
                    }

        return jsonBody

    # EDITABLE - Visualize/Graph/Human readable
    def report(self):
        pass
