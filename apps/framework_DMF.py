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
        self.MatchDegree:float = None

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


class CongestionEventDMF(DescriptiveMetricFormat):

    def __init__(self, unit: str, value=None, traits:list=[]):
        """Prefab for congestion"""
        super().__init__(name="congestion-event", unit=unit, value=value, traits=traits)


class CongestionFairnessDMF(DescriptiveMetricFormat):

    def __init__(self, unit: str, value=None, traits:list=[]):
        """Prefab for congestion fairness"""
        super().__init__(name="congestion-fairness", unit=unit, value=value, traits=traits)


class ThroughputDMF(DescriptiveMetricFormat):

    def __init__(self, unit: str, value=None, traits:list=[]):
        """Prefab for throughput"""
        super().__init__(name="throughput", unit=unit, value=value, traits=traits)


class DurationDMF(DescriptiveMetricFormat):

    def __init__(self, unit: str, value=None, traits:list=[]):
        """Prefab for duration"""
        super().__init__(name="duration", unit=unit, value=value, traits=traits)


class BandwidthDelayProductDMF(DescriptiveMetricFormat):

    def __init__(self, unit: str, value=None, traits:list=[]):
        super().__init__(name="bandwidth-delay-product", unit=unit, value=value, traits=traits)


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


def __findMatchingUnits(soughtUnit:str, soughtTraits:list, compareDMFs:List[DescriptiveMetricFormat]) -> list:
    """Look through a list of observation DMFs and try to find ones with the same unit that match, evaluate the match"""

    matches = []

    for compareDMF in compareDMFs:
        if compareDMF.Unit == soughtUnit:

            matchDegree = ((math.ceil(len(set(compareDMF.Traits) - set(soughtTraits))))/1)*100

            matches.append((compareDMF, matchDegree))

    matches.sort(key=lambda x: x[1])

    return matches


def __compareDMFs(dmf1:DescriptiveMetricFormat, dmf2:DescriptiveMetricFormat) -> float:
    """Do a basic comparison between DMFs"""
    return ((math.ceil(len(set(dmf1.Traits) - set(dmf2.Traits))))/1)*100


def __compareDMFtoDMFs(srcdmf:DescriptiveMetricFormat, compareDMFs:List[DescriptiveMetricFormat]) -> list:
    """Given a target DMF try create comparison across others"""

    matches = []

    for dmfMetric in compareDMFs:
        if dmfMetric.Name == srcdmf.Name:

            # Append the metric itself and the "trait match" degree (expressed as a number of traits asked for vs in metric)
            matchDegree = math.ceil(len(set(srcdmf.Traits) - set(dmfMetric.Traits)))

            matches.append((dmfMetric, matchDegree))

    matches.sort(key=lambda x: x[1])

    return matches


def __processConversionPath(srcDMF:DescriptiveMetricFormat, trgDMF:DescriptiveMetricFormat, observationDMFs: List[DescriptiveMetricFormat], conversionTree:dict=conversionTree) -> (DescriptiveMetricFormat, list):
    """Perform the process on the conversion path between point A and point B.
    :returns Resolved Metric (if found), list of warnings during operation
    """
    path = __resolveMetricPath(srcDMF.Unit, trgDMF.Unit, conversionTree)

    warnings = []
    retDMF = None

    if len(path) > 0:

        retDMF = copy.copy(srcDMF)
        retDMF.Name = trgDMF.Name

        # run ops along path, converting the unit
        for stepNum in range(0, len(path) - 1):
            step = path[stepNum]
            nextStep = path[stepNum + 1]
            operation = conversionTree[step][nextStep]
            retDMF.Value = operation(retDMF.Value, observationDMFs, retDMF, conversionTree)
            retDMF.Unit = nextStep
            retDMF.OpPath.append(step)
            retDMF.OpPath.append(nextStep)

    else:

        # check if any conversion was needed at all
        if srcDMF.Unit == trgDMF.Unit:
            # already present
            retDMF = srcDMF
        else:
            warnings.append("No Path from {}:{} to {}:{}".format(srcDMF.Name, srcDMF.Unit, trgDMF.Name, trgDMF.Unit))

    return retDMF, warnings


def __resolveDMFConversion(desiredMetric:DescriptiveMetricFormat, observationDMFs: List[DescriptiveMetricFormat], topLevelDesiredDMF:DescriptiveMetricFormat, conversionTree:dict=conversionTree) -> DescriptiveMetricFormat:
    """Given a desired metric, try to find the closest metric that can be converted, or find metrics that can generate the desired.
    :returns resolved metric (if able), the path these operations took, and the warnings
    """
    returnDMF = None

    # Try to find an metric that just requires a metric conversion
    matches = __compareDMFtoDMFs(desiredMetric, observationDMFs)

    if len(matches) > 0:
        # sort matches by match degree, and
        returnDMF = matches[0][0]
        returnDMF, unitConversionWarnings = __processConversionPath(returnDMF, desiredMetric, observationDMFs)
        topLevelDesiredDMF.Warnings.extend(unitConversionWarnings)
        if returnDMF is not None:
            if len(returnDMF.OpPath) > 0:
                topLevelDesiredDMF.OpPath.append(returnDMF.OpPath)

            topLevelDesiredDMF.OpPath.append("{}({}:{})".format(returnDMF.Name, returnDMF.Traits, returnDMF.Unit))
            topLevelDesiredDMF.Traits.extend(returnDMF.Traits)
    else:
        # have no matches, must then convert other metrics to this one
        metricAlternatives = __createConversionBFSTree(desiredMetric.Unit, conversionTree)

        # Check each alternative
        alternativeKeyIndex = 0
        keepLooking = True

        while keepLooking and alternativeKeyIndex < len(metricAlternatives):

            alternateMetricKey = list(metricAlternatives)[alternativeKeyIndex]

            # look through the observation for anything with matching units
            matches = __findMatchingUnits(alternateMetricKey, desiredMetric.Traits, observationDMFs)

            # try all the possible matches (the first one that resolves all the way, just take it)
            for matchDMF, matchDegree in matches:

                try:

                    returnDMF, alternateMetricWarnings = __processConversionPath(matchDMF, desiredMetric, observationDMFs)
                    topLevelDesiredDMF.Warnings.extend(alternateMetricWarnings)

                    if returnDMF is None:
                        # Could not resolve, move onto the next
                        raise Exception()
                    else:
                        # Found one, stop looking further
                        topLevelDesiredDMF.OpPath.extend(returnDMF.OpPath)
                        keepLooking = False
                        break

                except Exception as ex:
                    print('DMF: Cannot use alternative {} to {}'.format(alternateMetricKey, desiredMetric.Unit))
                    print(ex)

            alternativeKeyIndex += 1

    return returnDMF


def _getMetrics(desiredMetricDMFs:List[DescriptiveMetricFormat], observation:dict, conversionTree:dict=conversionTree, defaultValue=0) -> List[DescriptiveMetricFormat]:
    """Find a metric (or convert a metric) in an observation.
    Will construct the connectives from the metric, then try to find the closest metric from the observation
    :returns list of resolved metrics, list of unresolved desires, warnings
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
        copiedDesireMetric = DescriptiveMetricFormat(desiredMetric.Name, desiredMetric.Unit)

        if desiredMetric.Value is not None:
            copiedDesireMetric.Value = desiredMetric.Value
        else:
            copiedDesireMetric.Value = defaultValue

        resolvedMetric = __resolveDMFConversion(desiredMetric, dmfMetrics, copiedDesireMetric, conversionTree)

        if resolvedMetric is None:
            # Copy so we can assign the "default" fill in value
            resolvedMetrics.append(copiedDesireMetric)
            copiedDesireMetric.Warnings.append("Default Value of {} Assigned".format(copiedDesireMetric.Value))
        else:
            resolvedMetric.MatchDegree = __compareDMFs(resolvedMetric, desiredMetric)
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
    "gigabytes-per-second": {"megabits-per-second": lambda *x: x[0] * 1024},
    "":{"":0}
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

        if self.LogFileFullPath is not None:
            # Open file for appending
            firstLog = True

            # ensure paths is present
            if self.LogPath is not None:
                try:
                    os.makedirs(self.LogPath, exist_ok=True)
                except Exception as ex:
                    print('Agent: Error making directories. {}'.format(ex))

            if os.path.exists(self.LogFileFullPath):
                firstLog = False

            logFileFP = open(self.LogFileFullPath, 'a')

            if firstLog:
                # Write the header
                expandedHeader = None

                if self.ExpandObservationFields:
                    expandedHeader = ''

                    for metric in observationDMF.keys():
                        expandedHeader += '{},'.format(metric)

                if expandedHeader is None:
                    expandedHeader = 'DMF-Observation'

                logFileFP.write('Timestamp,Reward,Done,Info,{}\n'.format(expandedHeader))

            expandedFields = None

            if self.ExpandObservationFields:
                expandedFields = ''

                for metric in observationDMF.keys():

                    if type(observationDMF[metric]) is str:
                        expandedFields += '\"{}\",'.format(observationDMF[metric])
                    else:
                        expandedFields += '{},'.format(observationDMF[metric])

            if expandedFields is None:
                expandedFields = '\"{}\"'.format(observationDMF)

            logFileFP.write(
                '{},{},{},\"{}\",{}\n'.format(datetime.datetime.now().strftime("%d-%m-%Y-%H-%M-%S"), reward, done, info,
                                              expandedFields))

            logFileFP.flush()
            logFileFP.close()

        return observation, reward, done, info
