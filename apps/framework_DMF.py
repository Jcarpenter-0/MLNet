import copy
from typing import List
import apps
import math
import agents
import os
import datetime
import copy

# =============================
# Descriptive Metric Format
# =============================


class DescriptiveMetricFormat(object):

    def __init__(self, name:str, unit:str, value=None, traits:list=[]):
        """plain python object representation of the DMF"""
        self.Name:str = name
        # Traits: link-level, applicaton-level, user-generated
        self.Traits:list = traits
        # Units: bytes, bits, seconds, days, meters, farenhiet, packets, etc
        self.Unit:str = unit
        # Value
        self.Value = value

        # For identifying issues
        self.Warnings = []
        self.OpPath = []

    def GetDMFLabel(self, groupDeliminator:str= ":") -> str:
        """Serialize into simple "bar" delimited format for description"""
        return '{}{}{}{}{}'.format(self.Name, groupDeliminator, '|'.join(self.Traits), groupDeliminator, self.Unit)

    def ToDict(self) -> dict:
        """Convert to Dict"""
        return {self.GetDMFLabel():self.Value}


def ParseDMF(dmfLabel:str, dmfValue, groupDeliminator:str=":", subDeliminator:str="|") -> DescriptiveMetricFormat:
    """From the DMF serial format, convert to in-process format"""
    dmfPieces = dmfLabel.split(groupDeliminator)
    metricName = dmfPieces[0]
    traits = dmfPieces[1].split(subDeliminator)
    unit = dmfPieces[2]

    return DescriptiveMetricFormat(metricName, unit, dmfValue, traits)


#========================
# Some core DMF Metrics
# These help enforce the standard and provide quick definitions
#========================


class LatencyDMF(DescriptiveMetricFormat):

    def __init__(self, unit: str, value=None, traits:list=[]):
        """Prefab for latency"""
        super().__init__(name="latency", unit=unit, value=value, traits=traits)


class RoundTripTimeDMF(DescriptiveMetricFormat):

    def __init__(self, unit: str, value=None, traits:list=[]):
        """Prefab for rtt"""
        super().__init__(name="round-trip-time", unit=unit, value=value, traits=traits)


class LossDMF(DescriptiveMetricFormat):

    def __init__(self, unit: str, value=None, traits:list=[]):
        """Prefab for loss"""
        super().__init__(name="loss", unit=unit, value=value, traits=traits)


class ThroughputDMF(DescriptiveMetricFormat):

    def __init__(self, unit: str, value=None, traits:list=[]):
        """Prefab for throughput"""
        super().__init__(name="throughput", unit=unit, value=value, traits=traits)


class DurationDMF(DescriptiveMetricFormat):

    def __init__(self, unit: str, value=None, traits:list=[]):
        """Prefab for duration"""
        super().__init__(name="duration", unit=unit, value=value, traits=traits)


class DataSentDMF(DescriptiveMetricFormat):

    def __init__(self, unit: str, value=None, traits:list=[]):
        """Prefab for data"""
        super().__init__(name="data-sent", unit=unit, value=value, traits=traits)


class DataReceivedDMF(DescriptiveMetricFormat):

    def __init__(self, unit: str, value=None, traits:list=[]):
        """Prefab for data"""
        super().__init__(name="data-received", unit=unit, value=value, traits=traits)


class TargetAddressDMF(DescriptiveMetricFormat):

    def __init__(self, unit: str, value:str=None, traits:list=[]):
        """Prefab for address"""
        super().__init__(name="target-address", unit=unit, value=value, traits=traits)


class TargetPortDMF(DescriptiveMetricFormat):

    def __init__(self, unit: str, value:int=None, traits:list=[]):
        """Prefab for port"""
        super().__init__(name="target-port", unit=unit, value=value, traits=traits)


class TCPMinimumSendSizeDMF(DescriptiveMetricFormat):

    def __init__(self, unit: str, value=None, traits:list=[]):
        """Prefab for mss"""
        super().__init__(name="tcp-minimum-send-size", unit=unit, value=value, traits=traits)


class TimeStampDMF(DescriptiveMetricFormat):

    def __init__(self, unit: str, value=None, traits:list=[]):
        """Prefab for timestamp"""
        super().__init__(name="timestamp", unit=unit, value=value, traits=traits)


class ProtocolDMF(DescriptiveMetricFormat):

    def __init__(self, unit: str, value=None, traits:list=[]):
        """Prefab for protocol"""
        super().__init__(name="protocol", unit=unit, value=value, traits=traits)


class ParallelStreamsDMF(DescriptiveMetricFormat):

    def __init__(self, unit: str, value:int=None, traits:list=[]):
        """Prefab for parallel connections"""
        super().__init__(name="parallel-connections", unit=unit, value=value, traits=traits)


class PollRateDMF(DescriptiveMetricFormat):

    def __init__(self, unit: str, value:float=None, traits:list=[]):
        """Prefab for application/system's activity rate"""
        super().__init__(name="poll-rate", unit=unit, value=value, traits=traits)


class BufferSizeDMF(DescriptiveMetricFormat):

    def __init__(self, unit: str, value, traits:list=[]):
        """Prefab for buffer size"""
        super().__init__(name="buffer-size", unit=unit, value=value, traits=traits)


class BufferCapacityDMF(DescriptiveMetricFormat):

    def __init__(self, unit: str, value, traits:list=[]):
        """Prefab for buffer capacity, specifically whats in the buffer"""
        super().__init__(name="buffer-capacity", unit=unit, value=value, traits=traits)



# Conversion Tree is a "thruple" (metric, operation, metric2) in a one-direction, reverse for metric2 to metric1
# Fully initialized below methods
conversionTree = {}


def __createConversionBFSTree(rootMetric:str, conversionTree:dict=conversionTree) -> dict:
    """Build a bfs tree"""
    # new tree
    newTree = {}

    # seen
    seen = []

    # the bfs list
    if rootMetric in conversionTree.keys():
        processNext = {rootMetric:conversionTree[rootMetric]}

        while len(processNext.keys()) > 0:
            # process next node
            currentNodeName = list(processNext.keys())[0]

            seen.append(currentNodeName)

            currentNode = processNext.pop(currentNodeName)

            currentNodeConnections = list(currentNode.keys())

            # Add new branches
            for key in currentNodeConnections:
                if key not in seen:
                    newTree[key] = currentNodeName
                    processNext[key] = conversionTree[key]

    return newTree


def __resolveMetricPath(startMetric:str, endMetric:str, conversionTree:dict=conversionTree) -> list:
    """Using Breadth-First Search, traverse a conversionTree, create a new tree for operation resolution."""

    newTree = __createConversionBFSTree(endMetric, conversionTree)

    # return the path
    path = []

    if startMetric in newTree.keys():

        nextNode = startMetric

        while nextNode is not None:
            path.append(nextNode)

            if nextNode is not endMetric:
                nextNode = newTree[nextNode]
            else:
                nextNode = None

    return path


def __resolveDMFConversion(desiredMetric:DescriptiveMetricFormat, observationDMFs: List[DescriptiveMetricFormat], topLevelDesiredMetric:DescriptiveMetricFormat=None, conversionTree:dict=conversionTree) -> DescriptiveMetricFormat:
    """"""
    # check if any existing DMF's match the desired at the top level
    matches = []

    for dmfMetric in observationDMFs:
        if dmfMetric.Name == desiredMetric.Name:
            # Append the metric itself and the "trait match" degree (expressed as a number of traits asked for vs in metric)
            if topLevelDesiredMetric is not None:
                matchDegree = math.ceil(len(set(topLevelDesiredMetric.Traits) - set(dmfMetric.Traits)))
            else:
                matchDegree = math.ceil(len(set(desiredMetric.Traits) - set(dmfMetric.Traits)))

            matches.append((dmfMetric, matchDegree))

    returnDMF = None

    if len(matches) > 0:
        # sort matches by  match degree
        matches.sort(key=lambda x:x[1])

        returnDMF = matches[0][0]

        # ensure consistency of unit
        path = __resolveMetricPath(returnDMF.Unit, desiredMetric.Unit, conversionTree)

        # run ops along path
        for stepNum in range(0,len(path)-1):
            step = path[stepNum]
            nextStep = path[stepNum + 1]
            operation = conversionTree[step][nextStep]

            returnDMF.Value = operation(returnDMF.Value, observationDMFs, None, conversionTree)
            returnDMF.Unit = nextStep
            returnDMF.OpPath.append(step)

    else:
        # have none, must then convert other metrics to this one
        metricAlternatives = __createConversionBFSTree(desiredMetric.Unit, conversionTree)

        # try to find the closest alternative
        returnDMF = desiredMetric

        for key in metricAlternatives:

            matchingUnits = []

            # Find metrics that match the unit needed
            for observationDMF in observationDMFs:

                if observationDMF.Unit in key:

                    if topLevelDesiredMetric is not None:
                        matchDegree = math.ceil(len(set(topLevelDesiredMetric.Traits) - set(observationDMF.Traits)))
                    else:
                        matchDegree = math.ceil(len(set(desiredMetric.Traits) - set(observationDMF.Traits)))

                    matchingUnits.append((observationDMF, matchDegree))

            nextStepLabel = None

            matchingUnits.sort(key=lambda x: x[1])

            for observationDMF, matchDegree in matchingUnits:
                try:

                    # Found a metric, now attempt to convert it into what we need
                    path = __resolveMetricPath(observationDMF.Unit, desiredMetric.Unit, conversionTree)

                    # run ops along path
                    for stepNum in range(0, len(path) - 1):
                        step = path[stepNum]
                        nextStep = path[stepNum + 1]
                        nextStepLabel = nextStep
                        operation = conversionTree[step][nextStep]

                        #currentTraits = copy.copy(returnDMF.Traits)

                        # How do we resolve the "duration" check?
                        returnDMF.Value = operation(observationDMF.Value, observationDMFs, topLevelDesiredMetric, conversionTree)
                        returnDMF.Unit = nextStep
                        #returnDMF.Traits.extend(observationDMF.Traits)
                        returnDMF.OpPath.append(step)
                        dmfLog = 'Want {} {} in {} - Have {} {} in {} use? \"{} to {}:{}\"'.format(desiredMetric.Name, desiredMetric.Traits, desiredMetric.Unit, observationDMF.Name, observationDMF.Traits, observationDMF.Unit, step, nextStep, returnDMF.Traits)
                        print('DMF:' + dmfLog)
                        returnDMF.Warnings.append(dmfLog)

                    return returnDMF

                except Exception as ex:
                    print('DMF: Cannot use alternative {} to {}'.format(key, nextStepLabel))
                    print(ex)

    if returnDMF is not None and returnDMF.Value is None:
        returnDMF = None

    return returnDMF


def _getMetrics(desiredMetricDMFs:list, observation:dict, conversionTree:dict=conversionTree) -> List[DescriptiveMetricFormat]:
    """Find a metric (or convert a metric) in an observation.
    Will construct the connectives from the metric, then try to find the closest metric from the observation
    """

    # Convert observation to DMF list, for matching metric name of desired
    dmfMetrics = []

    for key in observation:

        try:
            newDMF = ParseDMF(key, observation[key])

            dmfMetrics.append(newDMF)
        except Exception as ex:
            print('DMF: Error Parsing a metric {}'.format(key))

    resolvedMetrics = []

    for desiredMetric in desiredMetricDMFs:
        resolvedMetric = __resolveDMFConversion(desiredMetric, dmfMetrics, None, conversionTree)

        if resolvedMetric is None:
            # Copy so we can assign the "default" fill in value
            copiedDesireMetric = copy.copy(desiredMetric)

            copiedDesireMetric.Value = 0

            resolvedMetrics.append(copiedDesireMetric)
        else:
            resolvedMetrics.append(resolvedMetric)

    return resolvedMetrics



fullConversions = {
    "bit":{"byte":lambda *x : x[0]/8, "kilobit":lambda *x : x[0]/1000, "bits-per-second": lambda *x: x[0]/__resolveDMFConversion(DurationDMF(unit='second'), x[1], x[2], x[3]).Value},
    "kilobit":{"bit":lambda *x : x[0]*1000, "megabit":lambda *x : x[0]/1000},
    "megabit": {"kilobit":lambda *x : x[0]*1000, "gigabit":lambda *x : x[0]/1000},
    "gigabit":{"megabit":lambda *x : x[0]*1000},
    "byte":{"bit":lambda *x : x[0]*8, 'bytes-per-second':lambda *x: x[0]/__resolveDMFConversion(DurationDMF(unit='second'), x[1], x[2], x[3]).Value, "kilobyte":lambda *x : x[0]/1024, "ethernet-packet":lambda *x : x[0]/1500, "ip-packet":lambda *x : x[0]/65535},
    "kilobyte":{"byte":lambda *x : x[0]*1024, "megabyte":lambda *x : x[0]/1024},
    "megabyte":{"kilobyte":lambda *x : x[0]*1024, "gigabyte":lambda *x : x[0]/1024},
    "gigabyte":{"megabyte":lambda *x : x[0]/1024},
    "nanosecond": {"millisecond":lambda *x : x[0]/1000},
    "millisecond":{"nanosecond":lambda *x : x[0]*1000, "second":lambda *x : x[0]/1000},
    "second":{"millisecond":lambda *x : x[0]*1000, "minute":lambda *x : x[0]/60},
    "minute":{"second":lambda *x : x[0]*60, "hour":lambda *x : x[0]/60},
    "hour":{"minute":lambda *x : x[0]*60, "day":lambda *x : x[0]/24},
    "day":{"hour":lambda *x : x[0]*24, "year":lambda *x : x[0]/365},
    "year":{"day":lambda *x : x[0]*365, "decade":lambda *x : x[0]/10},
    "decade":{"year":lambda *x : x[0]*24, "century":lambda *x : x[0]/10},
    "century":{"decade":lambda *x : x[0]*10},
    "ethernet-packet":{"byte":lambda *x : x[0]*1500},
    "ip-packet":{"byte":lambda *x : x[0]*65535},
    "bits-per-second":{"bit": lambda *x : x[0] * __resolveDMFConversion(DurationDMF(unit='second'), x[1], x[2], x[3]).Value, "kilobits-per-second":lambda *x : x[0]/1000},
    "kilobits-per-second": {"bits-per-second":lambda *x : x[0]*1000, "kilobits-per-second":lambda *x : x[0]/1000},
    "megabits-per-second":{"kilobits-per-second":lambda *x : x[0]*1000, "gigabits-per-second":lambda *x : x[0]/1000},
    "gigabits-per-second":{"megabits-per-second":lambda *x : x[0]*1000},
    "bytes-per-second": {"byte": lambda *x: x[0] * __resolveDMFConversion(DurationDMF(unit='second'), x[1], x[2], x[3]).Value,"kilobytes-per-second": lambda *x: x[0] / 1024},
    "kilobytes-per-second": {"bytes-per-second": lambda *x: x[0] * 1024, "megabytes-per-second": lambda *x: x[0] / 1024},
    "megabytes-per-second": {"kilobytes-per-second": lambda *x: x[0] * 1024,"gigabytes-per-second": lambda *x: x[0] / 1024},
    "gigabytes-per-second": {"megabits-per-second": lambda *x: x[0] * 1024}
}

conversionTree = conversionTree.update(fullConversions)


class AdaptationModule(agents.DomainModule):

    def __init__(self, desiredObservationMetrics:List[DescriptiveMetricFormat], logPath:str=None, logFileName:str=None, actionFields:dict=None, actionSpace:list=None):
        """Domain Module that will, given a desired set of observation metrics, attempt to ensure that any data coming in conforms that standard."""
        super().__init__(logPath, logFileName, actionFields, actionSpace)

        self.MiscInfo = []
        # the metrics you want, and the module will "enforce" as best as it is able
        self.DesiredObservations = desiredObservationMetrics

    def DefineReward(self, rawObservation:dict, observation:list) -> float:
        """Define the reward based on information from the observations"""
        return super().DefineReward(rawObservation, observation)

    def DefineDone(self, rawObservation:dict, observation:list) -> bool:
        """Determine if the agent's work is 'done', this is included for completness,
         but logically difficult in live systems. By default, returns False eg: not done."""
        return False

    def DefineInfo(self, rawObservation:dict) -> dict:
        """Raw information, agent state, and other misc information"""
        return {"domain-module": self, "raw-observation":rawObservation, "misc-info":self.MiscInfo}

    def DefineObservation(self, rawObservation:dict) -> (list, dict):
        """Use basic adaptation to ensure consistency of metrics"""

        dmfs = _getMetrics(self.DesiredObservations, rawObservation)

        observationDMF = {}

        observation = []

        for idx, resolved in enumerate(dmfs):

            # Match the names, this will truncate the "traits" but those can still be found in logging
            matchingDesired = copy.deepcopy(self.DesiredObservations[idx])

            matchingDesired.Value = resolved.Value

            observationDMF.update(matchingDesired.ToDict())
            observation.append(resolved.Value)

        return observation, observationDMF

    def Process(self, rawObservation: dict) -> (list, float, bool, dict):
        """Adapt system Process, includes an additional observation (dmf) alongside the other two"""
        observation, observationDMF = self.DefineObservation(rawObservation)

        reward = self.DefineReward(rawObservation=observationDMF, observation=observation)

        done = self.DefineDone(observationDMF, observation)

        info = self.DefineInfo(observationDMF)

        if self.LogPath is not None:
            # Open file for appending
            firstLog = True

            # ensure paths is present
            try:
                os.makedirs(self.LogPath, exist_ok=True)
            except Exception as ex:
                print('Agent-Server: Error making directories. {}'.format(ex))

            if os.path.exists(self.LogPath + self.LogFileName):
                firstLog = False

            logFileFP = open(self.LogPath + self.LogFileName, 'a')

            if firstLog:
                # Write the header
                logFileFP.write('Time-stamp,Raw-Observation,DMF-Observation,Reward,Done,Info\n'.format())

            logFileFP.write('{},\"{}\",{},{},{},\"{}\"\n'.format(datetime.datetime.now().strftime("%d-%m-%Y-%H-%M-%S"), rawObservation, observationDMF, reward, done, info))

            logFileFP.flush()
            logFileFP.close()

        return observation, reward, done, info
