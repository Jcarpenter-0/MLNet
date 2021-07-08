import numpy as np

import agents

import networks
import networks.mahimahi
import networks.mininet

import apps
import apps.Iperf3
import apps.Iperf
import apps.Ping


class __registryModule:

    def __init__(self, name:str=None, module:str=None, tags:list=[], metrics:list=[], configs:list=[]):
        self.Name:str = name
        self.Module:str = module
        self.Tags:list = tags
        self.Metrics:list = metrics
        self.Configs:list = configs

    def Populate(self, data:dict):
        self.Name = data['tool-name']
        self.Module = data['module']
        self.Tags = data['tags']
        self.Metrics = data['metrics']
        self.Configs = data['configs']

    def Match(self, soughtTags:list, soughtMetrics:list, configs:dict) -> float:
        """"""
        totalFields = len(self.Tags) + len(self.Metrics) + len(self.Configs)
        totalMatches = 0

        for soughtTag in soughtTags:
            if soughtTag in self.Tags:
                totalMatches+=1

        for soughtMetric in soughtMetrics:
            if soughtMetric in self.Metrics:
                totalMatches+=1

        for config in configs.keys():
            if config in self.Configs:
                totalMatches+=1

        return float(totalMatches/totalFields)


class __applicationModuleRegister(__registryModule):

    def Setup(self, setupArgs:dict, network:networks.NetworkModule, learner:agents.AgentWrapper, dirOffset='../../'):
        return NotImplementedError


class __iperfApplicationModuleRegister(__applicationModuleRegister):

    def Setup(self, setupArgs:dict, network:networks.NetworkModule, learner:agents.AgentWrapper, dirOffset='../../'):
        """Setup a client and server iperf pair. Will assume first and last nodes are the server and client"""

        firstNode:networks.Node = network.Nodes[0]
        lastNode:networks.Node = network.Nodes[-1]

        iperfClientArgs = []

        if 'protocol' in setupArgs.keys():
            if 'udp' in setupArgs['protocol']:
                iperfClientArgs.append('-u')

        iperfClientArgs.extend(['-c', firstNode.IpAddress, '-i', '0'])

        if 'duration' in setupArgs.keys():
            iperfClientArgs.append('-t')
            iperfClientArgs.append(setupArgs['duration'])

        if 'parallel connections' in setupArgs.keys():
            iperfClientArgs.append('-P')
            iperfClientArgs.append(setupArgs['parallel connections'])

        serverArg = ['iperf', '-s', '-i', '0']
        clientArg = apps.PrepWrapperCall('{}apps/Iperf.py'.format(dirOffset), iperfClientArgs, 100000, 'http://{}:{}'.format(firstNode.IpAddress, learner.LearnerPort))

        firstNode.AddApplication(learner.ToArgs())
        firstNode.AddApplication(serverArg)
        lastNode.AddApplication(clientArg)


class __iperf3ApplicationModuleRegister(__applicationModuleRegister):

    def Setup(self, setupArgs:dict, network:networks.NetworkModule, learner:agents.AgentWrapper, dirOffset='../../'):
        firstNode: networks.Node = network.Nodes[0]
        lastNode: networks.Node = network.Nodes[-1]

        iperfClientArgs = []

        if 'protocol' in setupArgs.keys():
            if 'udp' in setupArgs['protocol']:
                iperfClientArgs.append('-u')

        iperfClientArgs.extend(['-c', firstNode.IpAddress, '-i', '0'])

        if 'duration' in setupArgs.keys():
            iperfClientArgs.append('-t')
            iperfClientArgs.append(setupArgs['duration'])

        if 'parallel connections' in setupArgs.keys():
            iperfClientArgs.append('-P')
            iperfClientArgs.append(setupArgs['parallel connections'])

        serverArg = ['iperf3', '-s', '-i', '0']
        clientArg = apps.PrepWrapperCall('{}apps/Iperf3.py'.format(dirOffset), iperfClientArgs, 100000,
                                         'http://{}:{}'.format(firstNode.IpAddress, learner.LearnerPort))

        firstNode.AddApplication(learner.ToArgs())
        firstNode.AddApplication(serverArg)
        lastNode.AddApplication(clientArg)


class __pingApplicationModuleRegister(__applicationModuleRegister):

    def Setup(self, setupArgs:dict, network:networks.NetworkModule, learner:agents.AgentWrapper, dirOffset='../../'):
        firstNode: networks.Node = network.Nodes[0]
        lastNode: networks.Node = network.Nodes[-1]

        pingAmount = 10

        if 'count' in setupArgs.keys():
            pingAmount = setupArgs['count']

        packetSize = 56

        if 'packet size' in setupArgs.keys():
            packetSize = setupArgs['packet size']

        pingArgs = ['~dest', firstNode.IpAddress, '-c', pingAmount, '-s', packetSize, '-t', '255']

        clientArg = apps.PrepWrapperCall('{}apps/Ping.py'.format(dirOffset), pingArgs, 100000,
                                         'http://{}:{}'.format(firstNode.IpAddress, learner.LearnerPort))

        lastNode.AddApplication(clientArg)


class __networkModuleRegister(__registryModule):

    def Setup(self, setupArgs:dict, learner:agents.AgentWrapper, dirOffset='../../') -> networks.NetworkModule:
        """The call to setup the network, should result in a running network awaiting application calls"""
        return NotImplementedError


class __mahiMahiNetworkModuleRegister(__networkModuleRegister):

    def Setup(self, setupArgs:dict, learner:agents.AgentWrapper, dirOffset='../../') -> networks.NetworkModule:
        """Autobuilder method for creating a mahi mahi network"""

        shellList = []

        if 'link delay' in setupArgs.keys():
            shellList.append(networks.mahimahi.MahiMahiDelayShell(setupArgs['link delay']))

        if 'uplink loss' in setupArgs.keys():
            shellList.append(networks.mahimahi.MahiMahiLossShell(setupArgs['uplink loss']))

        if 'downlink loss' in setupArgs.keys():
            shellList.append(networks.mahimahi.MahiMahiLossShell(setupArgs['downlink loss'], 'downlink'))

        if 'uplink trace' in setupArgs.keys() and 'downlink trace' in setupArgs.keys():
            shellList.append(networks.mahimahi.MahiMahiLinkShell(setupArgs['uplink trace'], setupArgs['downlink trace']))

        node = networks.mahimahi.SetupMahiMahiNode(shellList, dirOffset=dirOffset)

        hostNode = networks.SetupLocalHost(dirOffset=dirOffset)

        mmModule = networks.NetworkModule(nodes=[hostNode, node])

        return mmModule


class __miniNetNetworkModuleRegister(__networkModuleRegister):

    def Setup(self, setupArgs:dict, learner:agents.AgentWrapper, dirOffset='../../') -> networks.NetworkModule:
        """Setup a mininet network, this will utilize many assumptions for the sake of speed,
         lower grain functionality is still easily doable via the component pieces."""

        if 'topology' in setupArgs.keys():

            nodeCount = None
            switchDensity = None

            if 'node count' in setupArgs.keys():
                nodeCount = setupArgs['node count']

            if 'hop count' in setupArgs.keys():
                switchDensity = setupArgs['hop count']

            topo = networks.mininet.MiniNetTopology(setupArgs['topology'], nodeCount=nodeCount, switchDensity=switchDensity)
        else:
            topo = networks.mininet.MiniNetTopology()

        return networks.mininet.SetupMiniNetNetwork(topo, dirOffset=dirOffset)


def __registerModules(envManifestFilePath:str='modules.csv', mainDelimister=',', subDelimiter='|', subDelimiterIndicator='s') -> dict:
    """Register the modules so that the auto builder may call upon them"""

    # Load the code logic of the modules first, then populate thier data dicts from the manifest
    modules = dict()

    modules[networks.mahimahi.__name__.split('.')[-1].lower()] = __mahiMahiNetworkModuleRegister()
    modules[networks.mininet.__name__.split('.')[-1].lower()] = __miniNetNetworkModuleRegister()
    modules[apps.Iperf3.__name__.split('.')[-1].lower()] = __iperf3ApplicationModuleRegister()
    modules[apps.Iperf.__name__.split('.')[-1].lower()] = __iperfApplicationModuleRegister()
    modules[apps.Ping.__name__.split('.')[-1].lower()] = __pingApplicationModuleRegister()

    # load in the manifest information
    fp = open(envManifestFilePath, 'r')
    modsRaw = fp.readlines()
    fp.close()

    headers = modsRaw[0].split(mainDelimister)[0:-1]

    modsRawData = modsRaw[1:]

    for modelLineRaw in modsRawData:

        modelLineRaw = modelLineRaw.replace('\n','')

        modelLineRawPieces = modelLineRaw.split(mainDelimister)

        moduleData = dict()

        for idx, header in enumerate(headers):
            moduleData[header] = None

            piece = modelLineRawPieces[idx]

            if subDelimiterIndicator in header:
                # sub-delim
                if subDelimiter in piece:
                    moduleData[header] = piece.split(subDelimiter)
                else:
                    if len(piece) > 0:
                        moduleData[header] = [piece]
                    else:
                        moduleData[header] = []
            else:
                moduleData[header] = piece

        try:
            module = modules[moduleData['tool-name'].lower()]

            module.Populate(moduleData.copy())

        except Exception as ex:
            print('Could not register {} : {}'.format(moduleData['tool-name'], str(ex)))

    return modules


def autoBuildEnv(learner:agents.AgentWrapper, soughtMetrics:list=[], networkArgs:dict={}, tags:list=[], fit:str= 'best', envManifestFilePath:str= 'modules.csv', dirOffset='../../', skipApps=False) -> networks.NetworkModule:
    """Attempt to build an environment for you based on what type of fit
    :return list of Nodes"""

    modules = __registerModules(envManifestFilePath)

    # find the tool that best matches what is being asked for
    # tuples of 'module index', 'match value'
    hosts = []
    applications = []

    for idx, moduleName in enumerate(modules):
        module = modules[moduleName]

        if module.Module == 'Host':
            hosts.append([module.Match(tags, soughtMetrics, networkArgs),moduleName])
        elif module.Module == 'Application':
            applications.append([module.Match(tags, soughtMetrics, networkArgs),moduleName])

    # get highest value pieces
    hostMaxIndex = np.argmax(hosts, axis=0)[0]
    appMaxIndex = np.argmax(applications, axis=0)[0]

    hostMaxVal = hosts[hostMaxIndex][0]
    appMaxVal = applications[appMaxIndex][0]

    selectedNetwork:__networkModuleRegister = modules[hosts[hostMaxIndex][1]]
    selectedApplication:__applicationModuleRegister = modules[applications[appMaxIndex][1]]

    if fit is 'absolute':

        if hostMaxVal < 1.0 or appMaxVal < 1.0:
            selectedNetwork: __networkModuleRegister = None
            selectedApplication: __applicationModuleRegister = None

    network = None

    if selectedNetwork is not None:
        # setup the networks
        network = selectedNetwork.Setup(networkArgs, learner, dirOffset)

        if skipApps is False and selectedApplication is not None:
            # setup the applications' args on the network nodes
            selectedApplication.Setup(networkArgs, network, learner, dirOffset)


    print('{} match {} - {} ready'.format(fit, selectedNetwork.Name, selectedApplication.Name))

    return network
