class network:

    def __init__(self, server, client):

        self.Server = server
        self.Client = client

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