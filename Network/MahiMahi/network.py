import subprocess
import os

class network:

    def __init__(self, server, client):
        # number of Iperf servers to start up
        self.Delay = 0
        self.CC = None
        self.LogFileFullPath = './tmp/epoch-network-Log.json'
        self.LossRateUplink = 0.01
        self.LossRateDownlink = 0.01
        self.BandwidthTraceFileUplink = None
        self.BandwidthTraceFileDownlink = None
        self.process = None
        self.Server = server
        self.Client = client

        self.OldCC = None


    def setup(self):
        subprocess.check_output('sudo sysctl -w net.ipv4.ip_forward=1', shell=True)


    def run(self):

        # change the system congestion control

        ccCmdRes = subprocess.check_output('sysctl net.ipv4.tcp_congestion_control', shell=True)

        ccCmdRes = ccCmdRes.decode("utf-8")

        ccName = ccCmdRes.split('=')[-1].replace(' ', '')
        ccName = ccName.replace('\n', '')

        self.OldCC = ccName

        # take current CC for notation purposes
        if self.CC is None:
            self.CC = ccName

        subprocess.check_output('sudo sysctl -w net.ipv4.tcp_congestion_control=' + self.CC, shell=True)

        # MahiMahi Commands
        basemmcommand = ['mm-loss', 'uplink', str(self.LossRateUplink), 'mm-loss', 'downlink', str(self.LossRateDownlink)]

        if self.BandwidthTraceFileDownlink is not None and self.BandwidthTraceFileUplink is not None:
            basemmcommand.extend(['mm-link', self.BandwidthTraceFileUplink, self.BandwidthTraceFileDownlink])

        # run the client run package
        if len(self.Client.Command) > 0:
            basemmcommand.extend(self.Client.Command)

        self.process = subprocess.Popen(basemmcommand)

        self.process.wait()

    def shutdown(self):
        self.process.kill()
        self.process.wait()

        # restore old CC
        subprocess.check_output('sudo sysctl -w net.ipv4.tcp_congestion_control=' + self.OldCC, shell=True)

    def log(self):

        jsonBody = {'setup': {'msDelay': self.Delay,
                              'expcongestionControl': self.CC,
                              'syscongestionControl': self.OldCC,
                              'lossRateUplink': self.LossRateUplink,
                              'lossRateDownlink': self.LossRateDownlink,
                              'upLinkTraceFile': self.BandwidthTraceFileUplink,
                              'downLinkTraceFile': self.BandwidthTraceFileDownlink},
                    'logs': {}
                    }

        return jsonBody

    # EDITABLE - Visualize/Graph/Human readable
    def report(self):

        pass