class network:

    def __init__(self):

        self.AvailableThroughput = 10

        self.Server = None
        self.Client = None

    def setup(self):
        pass

    def run(self):

        self.Client.run()

    def shutdown(self):
        pass

    def log(self):

        jsonBody = {'setup': {},
                    'logs': {'NetworkRewardVariable':self.AvailableThroughput}
                    }

        return jsonBody

    # EDITABLE - Visualize/Graph/Human readable
    def report(self):
        pass