
# https://wiki.linuxfoundation.org/networking/netem

import networks


class NetemNetwork(networks.NetworkSetup):

    def Setup(self, configs:dict) -> (networks.Network, list, float, list):
        return