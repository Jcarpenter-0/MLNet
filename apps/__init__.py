import requests
import json
import sys
import subprocess
import time
import numpy as np


def ToPopenArgs(argDict:dict, replacer:str='~') -> list:
    """Takes the current args, and converts it to a list of commands suitable for a Popen command call. Any args with the key ! instead of - will have only the value passed."""

    # Formatted as ['argName', 'argVal']
    cmdList = list()
    print(argDict)

    for idx, arg in enumerate(argDict.keys()):

        if replacer not in arg:
            cmdList.append(arg)

        argVal = argDict[arg]

        if argVal is not None:
            cmdList.append('{}'.format(argVal))

    return cmdList


def PrepGeneralWrapperCall(commandFilePath:str,
                           targetServerAddress:str=None, targetServerPort:int=None, targetServerPath:str=None,
                           agentServerAddress:str=None, agentServerPort:int=None,
                           probingApproach:int=None, probingInterface:str=None, runDuration:int=None,
                           protocol:str=None, parallelTCPConnections:int=None, logFilePath:str=None,
                           additionalArgs:dict=None, dirOffset:str='./../../', removeNones:bool=True) -> list:
    """Using the "general" language of parameters create a process call friendly command.
    Any "parameter" that overlaps with two or more applications idealily should bere."""

    commandList = ['python3', '{}{}'.format(dirOffset, commandFilePath)]

    commandArgs = dict()

    #General Action Format (GAF) ~ Use to create as close to a core set of action standard labels as we can
    #The specifics of these parameters are realized at the application wrapper level where they are converted into runtime args
    commandArgs['-target-server-address'] = targetServerAddress
    commandArgs['-target-server-path'] = targetServerPath
    commandArgs['-target--server-request-port'] = targetServerPort
    commandArgs['-agent-address'] = agentServerAddress
    commandArgs['-agent-port'] = agentServerPort
    commandArgs['-probing-approach'] = probingApproach
    commandArgs['-probing-interface'] = probingInterface
    commandArgs['-run-duration-seconds'] = runDuration
    commandArgs['-protocol'] = protocol
    commandArgs['-parallel-tcp-connections'] = parallelTCPConnections
    commandArgs['-logfile-path'] = logFilePath

    if additionalArgs is not None:
        commandArgs.update(additionalArgs)

    if removeNones:
        # remove the "none"s
        for key in commandArgs.copy():
            if commandArgs[key] is None:
               del commandArgs[key]

    # Last n args are agent specific
    commandList.append(json.dumps(commandArgs))

    return commandList


def ParseDefaultArgs(readArgs:list) -> dict:
    """Parse out the basic command line arguements feed into an application wrapper"""

    # Get the json formatted args dict
    rawArgs = readArgs[-1]

    args = json.loads(rawArgs)

    print('App Args full: {}'.format(args))

    return args


def ParseTCPDump(filePath:str) -> dict:
    """Parse TCPDump Log files"""

    # Read the monitor file
    monitorFP = open(filePath, 'r')

    monitorRawData = monitorFP.readlines()

    monitorFP.close()

    timeStamps = []
    packetProtocols = []
    packetSizes = []
    sequenceNumbers = []

    packetSeqMetas = []
    packetAckMetas = []

    for idx, line in enumerate(monitorRawData):

        line = line.replace('\n','')

        if 'udp' in line:
            packetProtocols.append('UDP')
        elif 'seq' in line or 'ack' in line:
            packetProtocols.append('TCP')

        if 'length' in line:
            length = line.split('length ')[-1]

            if ':' in length:
                length = length.split(':')[0]

            length = int(length)

            if length == 0:
                # Minimum size
                length = 21

            packetSizes.append(length)

            # disect the line
            linePieces = line.split(' ')

            ts = linePieces[0].split(':')

            tsHours = int(ts[0])
            tsMinutes = int(ts[1])
            tsSeconds = float(ts[2])
            firstTimeSeconds = tsSeconds + (60 * tsMinutes) + (60 * 60 * tsHours)

            packetMeta = {'timestamp-seconds': firstTimeSeconds}

            # Sender
            if 'seq' in line:
                seqNum = line.split('seq')[1].split(':')[0].split(',')[0]

                sequenceNumbers.append(int(seqNum))

                packetMeta['seqNum'] = seqNum

                packetSeqMetas.append(packetMeta)

            # Response
            if 'ack' in line and 'seq' not in line:
                ackNum = line.split('ack')[1].split(',')[0]

                packetMeta['ackNum'] = ackNum

                packetAckMetas.append(packetMeta)

            timeStamps.append(linePieces[0])


    dataDict = {}

    # Calculate the duration by difference of first and last timestamp
    firstTS = timeStamps[0].split(':')

    firstTSHours = int(firstTS[0])
    firstTSMinutes = int(firstTS[1])
    firstTSSeconds = float(firstTS[2])
    firstTimeSeconds = firstTSSeconds + (60 * firstTSMinutes) + (60 * 60 * firstTSHours)

    lastTS = timeStamps[-1].split(':')

    lastTSHours = int(lastTS[0])
    lastTSMinutes = int(lastTS[1])
    lastTSSeconds = float(lastTS[2])
    lastTimeSeconds = lastTSSeconds + (60 * lastTSMinutes) + (60 * 60 * lastTSHours)

    # Last - First Timestamps
    dataDict['collection-duration-seconds'] = abs(lastTimeSeconds - firstTimeSeconds)

    latencies = []

    # Using matched seqNum ackNum pairs get estimate of latency by differences in time stamps
    for seq in packetSeqMetas:

        # find the matching seqNum among the Acks if any
        for ack in packetAckMetas:

            if seq['seqNum'] == ack['ackNum']:
                # Match found, put timebetween into list
                latencies.append(abs(float(ack['timestamp-seconds'] - seq['timestamp-seconds'])))

    dataDict['latency|packet-analyzer|link|per-packet|average'] = np.mean(latencies)

    # Count duplicate sequence numbers (unique - all)
    dataDict['loss|packet-analyzer|link|per-packet-pair|difference-of-unique-sequence-numbers'] = len(sequenceNumbers) - len(np.unique(sequenceNumbers))

    dataDict['transfered-bytes|packet-analyzer|link|per-packet|sum'] = np.sum(packetSizes)

    dataDict['throughput|packet-analyzer|link|per-second|sum|divided-over-duration'] = np.sum(packetSizes)/dataDict['collection-duration-seconds']

    return dataDict


def ParseIperf3Output(rawData: bytes, args: dict) -> dict:

    outputRaw = rawData.decode()

    # get output from the logfile
    if '--logfile' in args.keys():
        logFileFP = open(args['--logfile'], 'r')
        output = json.load(logFileFP)
        logFileFP.close()
    else:
        output = json.loads(outputRaw)

    dataDict = dict()

    startSection = output['start']

    dataDict['target-address'] = startSection['connecting_to']['host']
    dataDict['target-port'] = startSection['connecting_to']['port']
    dataDict['version'] = startSection['version']
    dataDict['time'] = "{}".format(startSection['timestamp']['time'])
    dataDict['timesecs'] = startSection['timestamp']['timesecs']
    dataDict['tcp_mss_default'] = startSection['tcp_mss_default']

    dataDict['protocol'] = startSection['test_start']['protocol']
    dataDict['parallel-tcp-connections'] = startSection['test_start']['num_streams']
    dataDict['blksize'] = startSection['test_start']['blksize']
    dataDict['omit'] = startSection['test_start']['omit']
    dataDict['duration|seconds'] = startSection['test_start']['duration']
    dataDict['bytes'] = startSection['test_start']['bytes']
    dataDict['blocks'] = startSection['test_start']['blocks']
    dataDict['reverse'] = startSection['test_start']['reverse']

    endSection = output['end']

    sendSection = endSection['sum_sent']

    dataDict['sender-duration|second'] = sendSection['seconds']
    dataDict['sender-received-data|byte'] = sendSection['bytes']
    dataDict['sender-throughput|bits-per-second'] = sendSection['bits_per_second']
    dataDict['loss|sender-retransmits'] = sendSection['retransmits']

    recSection = endSection['sum_received']

    dataDict['receiver-duration|second'] = recSection['seconds']
    dataDict['receiver-received-data|byte'] = recSection['bytes']
    dataDict['receiver-throughput|bits-per-second'] = recSection['bits_per_second']

    # Stream dissection
    streamSection = endSection['streams']

    minRTTs = []
    maxRTTs = []
    avgRTTs = []

    maxSendCWNDs = []

    for stream in streamSection:
        streamSender = stream['sender']

        snd = int(streamSender['max_snd_cwnd'])
        maxSendCWNDs.append(snd)

        # RTTs are in usec (microseconds)
        maxRTT = int(streamSender['max_rtt'])
        maxRTTs.append(maxRTT)

        minRTT = int(streamSender['min_rtt'])
        minRTTs.append(minRTT)

        meanRTT = int(streamSender['mean_rtt'])
        avgRTTs.append(meanRTT)

    # Calculate macros
    dataDict['Round-trip-time|application-level|maximum'] = float(np.mean(maxRTTs))
    dataDict['Round-trip-time|application-level|minimum'] = float(np.mean(minRTTs))
    dataDict['Round-trip-time|application-level|mean'] = float(np.mean(avgRTTs))
    dataDict['tcp-send-congestion-window|max'] = int(np.max(maxSendCWNDs))
    dataDict['tcp-send-congestion-window|mean'] = float(np.mean(maxSendCWNDs))
    dataDict['tcp-send-congestion-window|minimum'] = int(np.min(maxSendCWNDs))

    dataDict['system_info'] = "\"{}\"".format(startSection['system_info'])

    return dataDict

# =============================
# Descriptive Metric Format
# =============================


class DescriptiveMetricFormat(object):

    def __init__(self, name:str, value=None, traits:list=[], units:list=[]):
        """plain python object representation of the DMF"""
        self.Name:str = name
        # Traits: link-level, applicaton-level, user-generated
        self.Traits:list = traits
        # Units: bytes, bits, seconds, days, meters, farenhiet, packets, etc
        self.Units:list = units
        # Value
        self.Value = value

    def SerializeDMF(self, groupDeliminator:str=":") -> str:
        """Serialize into simple "bar" delimited format for description"""
        return '{}{}{}{}{}'.format(self.Name, groupDeliminator, '|'.join(self.Traits), groupDeliminator, '|'.join(self.Units))

    def ToDict(self) -> dict:
        """Convert to Dict"""
        return {self.SerializeDMF():self.Value}


def ParseDMF(dmfLabel:str, dmfValue, groupDeliminator:str=":", subDeliminator:str="|") -> DescriptiveMetricFormat:
    """From the DMF serial format, convert to in-process format"""
    dmfPieces = dmfLabel.split(groupDeliminator)
    metricName = dmfPieces[0]
    traits = dmfPieces[1].split(subDeliminator)
    units = dmfPieces[2].split(subDeliminator)

    return DescriptiveMetricFormat(metricName, dmfValue, traits, units)


class CoreDMFMetrics(object):

    def __init__(self, latency:DescriptiveMetricFormat, loss:DescriptiveMetricFormat, throughput:DescriptiveMetricFormat, dataTransfered:DescriptiveMetricFormat, duration:DescriptiveMetricFormat):
        """The core networking metrics"""
        self.Latency:DescriptiveMetricFormat = latency
        self.Loss:DescriptiveMetricFormat = loss
        self.Throughput:DescriptiveMetricFormat = throughput
        self.DataTransfered:DescriptiveMetricFormat = dataTransfered
        self.Duration:DescriptiveMetricFormat = duration


# =============================
# Action Adaptive Systems
# =============================

# PENDING

# =============================

class App(object):

    def __init__(self):
        """The representation of an application's execution"""

    def TranslateAction(self, gafField:str, gafActions:dict, targetParameter:str, targetDict:dict):
        """Default action translate, just look for x paramter in GAF then replace set the parameter to a localized para value"""
        if gafField in gafActions.keys():
            targetDict[targetParameter] = gafActions[gafField]

    def TranslateActions(self, args:dict) -> (dict, list):
        """Translate framework general arguements into app specific arguements.
        Example: -C -Z are both flags for congestion control in Iperf versions, we want a general --congestion-control.
        By default, will just do nothing."""
        return args, []

    def Run(self, runArgs:dict) -> (dict, list):
        """Run the application and return the metrics it has/collects and the warnings."""
        return NotImplementedError


def RunApplication(application:App, runCount:int=10000):
    """Parse args, run application, send results, handle additional monitoring"""

    args = ParseDefaultArgs(sys.argv)

    retryCount = 3
    retriesRemaining = retryCount
    retryDelay = 1

    fullFailure = False

    # run n times, allows the controller to "explore" the environment
    currentRunNum = 0
    while(currentRunNum < runCount):

        exception = False

        monitorData = None
        probingProc = None

        try:

            # If probing approach is passive, start it before the application runs
            if(args['-probing-approach'] == 1):

                probingProc = subprocess.Popen(['sudo', 'tcpdump', '-i', args['-probing-interface'], '-l', '-v', './link-monitoring.txt'])

            commands, gaps = application.TranslateActions(args)

            print('Application: Translation Gaps: {}'.format(gaps))

            result, warnings = application.Run(commands)

            print("Application: Warnings {}".format(warnings))

            # If probing approach is passive, end it for packaging
            if (args['-probing-approach'] == 1):

                probingProc.kill()

                monitorData = ParseTCPDump('./link-monitoring.txt')


            # If probing approach is active, probe AFTER the application has done stuff
            elif (args['-probing-approach'] == 2):
                probingProc = subprocess.Popen(
                    ['iperf3', '-c', args['-probing-interface'], '-J', '--logfile', './link-monitoring.json'])

                try:
                    probingProc.wait()
                except exception as ex:
                    probingProc.kill()

                # load the json data and pull out relevant features
                iperfJSFP = open('./link-monitoring.json', 'r')
                monitorData = ParseIperf3Output(json.load(iperfJSFP), args)
                iperfJSFP.close()

            # Format resultant data into sending form
            collectedData = {'application-data': result}

            # Add Gap and Warning Data
            collectedData['application-warnings'] = warnings
            collectedData['application-gaps'] = gaps

            # Add monitoring data
            if monitorData is not None:
                collectedData['monitor-data'] = monitorData

            if args['-agent-address'] is not None:

                # Send to agent, and get new action
                jsonData = json.dumps(collectedData)

                response = requests.post('http:{}:{}/'.format(args['-agent-address'], args['-agent-port']), data=jsonData)

                respDict = json.loads(response.content.decode())

                "Update the command line args with new args, will replace any matches and add missing"
                updatedArgs = args.copy()

                if isinstance(respDict, dict):

                    for key in respDict.keys():
                        updatedArgs[key] = respDict[key]

                args = updatedArgs

            currentRunNum += 1

            # Refresh retries
            retriesRemaining = retryCount
        except KeyboardInterrupt as inter:
            raise inter
        except subprocess.CalledProcessError as ex:
            exception = True
            print(ex)
        except Exception as ex1:
            exception = True
            fullFailure = True
            print(ex1)

        finally:

            if exception and not fullFailure:

                if retriesRemaining > 0:
                    time.sleep(retryDelay)
                    print('Retrying')
                    retriesRemaining = retriesRemaining - 1
                else:
                    print('Failure')
                    currentRunNum = runCount
                    raise Exception('Ran out of retries')
            elif fullFailure:
                currentRunNum = runCount
                raise Exception('Closed')
