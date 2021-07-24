import requests
import json
import sys
import subprocess
import time
import numpy as np
import apps.framework_DMF


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


def _prepGeneralWrapperCall(commandFilePath:str, args:dict, dirOffset:str='./../../') -> list:
    """Takes a dict of GAF formatted commands, and unpacks them into a command line ready list"""

    commandList = ['python3', '{}{}'.format(dirOffset, commandFilePath)]

    # Last n args are agent specific
    basicJson = json.dumps(args)

    # add escaped escaped quotes to help the shell digest the json
    basicJson = basicJson.replace('\"', '\\\"')

    commandList.append("\"{}\"".format(basicJson))

    return commandList


def PrepGeneralWrapperCall(commandFilePath:str,
                           targetServerAddress:str=None, targetServerPort:int=None, targetServerPath:str=None,
                           agentServerAddress:str=None, agentServerPort:int=None,
                           probingApproach:int=None, probingInterface:str=None, runDuration:int=None,
                           protocol:str=None, parallelTCPConnections:int=None, logFilePath:str=None, pollRate:float=None,
                           additionalArgs:dict=None, dirOffset:str='./../../', removeNones:bool=True) -> list:
    """Using the "general" language of parameters create a process call friendly command.
    Any "parameter" that overlaps with two or more applications idealily should bere."""

    commandArgs = dict()

    #General Action Format (GAF) ~ Use to create as close to a core set of action standard labels as we can
    #The specifics of these parameters are realized at the application wrapper level where they are converted into runtime args
    commandArgs['-target-server-address'] = targetServerAddress
    commandArgs['-target-server-path'] = targetServerPath
    commandArgs['-target-server-request-port'] = targetServerPort
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
                print('Framework: Prepping call: removing {} {}'.format(key, commandArgs[key]))
                del commandArgs[key]

    return _prepGeneralWrapperCall(commandFilePath, commandArgs, dirOffset)


def ParseDefaultArgs(readArgs:list) -> dict:
    """Parse out the basic command line arguements feed into an application wrapper"""

    # Get the json formatted args dict
    rawArgs = readArgs[-1]
    args = json.loads(rawArgs)

    #print('App Args full: {}'.format(args))

    return args


def getCC() -> str:

    ccsRaw = subprocess.check_output(['sysctl', 'net.ipv4.tcp_congestion_control'])

    ccsRaw = ccsRaw.decode()

    # net.ipv4.tcp_congestion_control = cubic
    ccRawPieces = ccsRaw.split('=')[-1]

    ccRawPieces = ccRawPieces.lstrip()

    ccRawPieces = ccRawPieces.replace('\n', '')

    return ccRawPieces


def getCCs() -> list:

    ccsRaw = subprocess.check_output(['sysctl', 'net.ipv4.tcp_available_congestion_control'])

    ccsRaw = ccsRaw.decode()

    # example result: net.ipv4.tcp_available_congestion_control = reno cubic
    ccRawPieces = ccsRaw.split('=')[-1]

    ccRawPieces = ccRawPieces.lstrip()

    currentCongestionControlFlavors = ccRawPieces.split(' ')

    return currentCongestionControlFlavors


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
    duration = abs(lastTimeSeconds - firstTimeSeconds)
    dataDict.update(apps.framework_DMF.DurationDMF(value=duration, unit='second', traits=['network-level', 'link-sum']).ToDict())

    latencies = []

    # Using matched seqNum ackNum pairs get estimate of latency by differences in time stamps
    for seq in packetSeqMetas:

        # find the matching seqNum among the Acks if any
        for ack in packetAckMetas:

            if seq['seqNum'] == ack['ackNum']:
                # Match found, put timebetween into list
                latencies.append(abs(float(ack['timestamp-seconds'] - seq['timestamp-seconds'])))

    dataDict.update(apps.framework_DMF.RoundTripTimeDMF(value=np.mean(latencies), unit='second', traits=['network-level', 'link-sum', 'average']).ToDict())

    # Count duplicate sequence numbers (unique - all)
    dataDict.update(apps.framework_DMF.LossDMF(value=len(sequenceNumbers) - len(np.unique(sequenceNumbers)), unit='packet', traits=['network-level', 'link-sum', 'difference-of-unique-sequence-numbers']).ToDict())
    dataDict.update(apps.framework_DMF.DataSentDMF(value=np.sum(packetSizes), unit='packet', traits=['network-level', 'link-sum']).ToDict())
    dataDict.update(apps.framework_DMF.ThroughputDMF(value=np.sum(packetSizes)/duration, unit='byte-per-second', traits=['network-level', 'link-sum']).ToDict())

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

    dataDict.update(apps.framework_DMF.TargetAddressDMF(value=startSection['connecting_to']['host'], unit='IP', traits=['application-level']).ToDict())
    dataDict.update(apps.framework_DMF.TargetPortDMF(value=startSection['connecting_to']['port'], unit='Port', traits=['application-level']).ToDict())

    dataDict['version'] = startSection['version']

    dataDict.update(apps.framework_DMF.TimeStampDMF(value=startSection['timestamp']['time'], unit='date-time', traits=['application-level','day-of-week, day month-abbreviated year, hour:minute:second GMT']).ToDict())
    dataDict.update(apps.framework_DMF.TimeStampDMF(value=startSection['timestamp']['timesecs'], unit='second', traits=['application-level','epoch-seconds']).ToDict())
    dataDict.update(apps.framework_DMF.TCPMinimumSendSizeDMF(value=startSection['tcp_mss_default'], unit='byte', traits=['application-level', 'default']).ToDict())
    dataDict.update(apps.framework_DMF.ProtocolDMF(value=startSection['test_start']['protocol'], unit='transport-layer', traits=['application-level', 'transport-layer']).ToDict())
    dataDict.update(apps.framework_DMF.ParallelStreamsDMF(value=startSection['test_start']['num_streams'], unit='tcp-stream', traits=['application-level', 'transport-layer']).ToDict())

    dataDict['blksize'] = startSection['test_start']['blksize']
    dataDict['omit'] = startSection['test_start']['omit']
    dataDict['bytes'] = startSection['test_start']['bytes']
    dataDict['blocks'] = startSection['test_start']['blocks']
    dataDict['reverse'] = startSection['test_start']['reverse']

    dataDict.update(apps.framework_DMF.DurationDMF(value=float(startSection['test_start']['duration']), unit='second', traits=['application-level']).ToDict())

    endSection = output['end']

    sendSection = endSection['sum_sent']

    dataDict.update(apps.framework_DMF.DurationDMF(value=float(sendSection['seconds']), unit='second', traits=['application-level', 'sender']).ToDict())
    dataDict.update(apps.framework_DMF.DataSentDMF(value=float(sendSection['bytes']), unit='byte', traits=['sender', 'application-level']).ToDict())
    dataDict.update(apps.framework_DMF.ThroughputDMF(value=float(sendSection['bits_per_second']), unit='bits-per-second', traits=['application-level', 'sender']).ToDict())
    dataDict.update(apps.framework_DMF.LossDMF(value=float(sendSection['retransmits']), unit='retransmits', traits=['application-level', 'sender']).ToDict())

    recSection = endSection['sum_received']

    dataDict.update(apps.framework_DMF.DurationDMF(value=float(recSection['seconds']), unit='second', traits=['application-level', 'receiver']).ToDict())
    dataDict.update(apps.framework_DMF.DataReceivedDMF(value=float(recSection['bytes']), unit='byte', traits=['receiver', 'application-level']).ToDict())
    dataDict.update(apps.framework_DMF.ThroughputDMF(value=float(recSection['bits_per_second']), unit='bits-per-second', traits=['application-level', 'receiver']).ToDict())

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
    dataDict.update(apps.framework_DMF.RoundTripTimeDMF(value=float(np.mean(maxRTTs)), unit='millisecond', traits=['round-trip-time', 'application-level', 'maximum']).ToDict())
    dataDict.update(apps.framework_DMF.RoundTripTimeDMF(value=float(np.mean(minRTTs)), unit='millisecond', traits=['round-trip-time', 'application-level', 'minimum']).ToDict())
    dataDict.update(apps.framework_DMF.RoundTripTimeDMF(value=float(np.mean(avgRTTs)), unit='millisecond', traits=['round-trip-time', 'application-level', 'average']).ToDict())

    dataDict.update(apps.framework_DMF.DescriptiveMetricFormat(name='tcp-send-congestion-window', value=int(np.max(maxSendCWNDs)), unit='congestion-window-unit', traits=['application-level', 'maximum']).ToDict())
    dataDict.update(apps.framework_DMF.DescriptiveMetricFormat(name='tcp-send-congestion-window', value=float(np.mean(maxSendCWNDs)), unit='congestion-window-unit', traits=['application-level', 'average']).ToDict())
    dataDict.update(apps.framework_DMF.DescriptiveMetricFormat(name='tcp-send-congestion-window', value=int(np.min(maxSendCWNDs)), unit='congestion-window-unit', traits=['application-level', 'minimum']).ToDict())

    dataDict['system_info'] = "\"{}\"".format(startSection['system_info'])

    return dataDict

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
            if( '-probing-approach' in args.keys() and args['-probing-approach'] == 1):

                probingProc = subprocess.Popen(['sudo', 'tcpdump', '-i', args['-probing-interface'], '-l', '-v', './link-monitoring.txt'])

            commands, gaps = application.TranslateActions(args)
            result, warnings = application.Run(commands)

            result.update(args)

            if gaps is not None and len(gaps) > 0:
                print('Application: Translation Gaps: {}'.format(gaps))

            if warnings is not None and len(warnings) > 0:
                print("Application: Warnings {}".format(warnings))

            # If probing approach is passive, end it for packaging
            if ('-probing-approach' in args.keys() and args['-probing-approach'] == 1):
                probingProc.kill()
                monitorData = ParseTCPDump('./link-monitoring.txt')

            # If probing approach is active, probe AFTER the application has done stuff
            elif ('-probing-approach' in args.keys() and args['-probing-approach'] == 2):
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
            collectedData = result

            # Add Gap and Warning Data
            #collectedData['application-warnings'] = warnings.extend(gaps)
            #collectedData['command-issued'] = args

            # Add monitoring data
            if monitorData is not None:
                collectedData.update(monitorData)

            if args['-agent-address'] is not None:

                # Send to agent, and get new action
                jsonData = json.dumps(collectedData)

                response = requests.post('http://{}:{}/'.format(args['-agent-address'], args['-agent-port']), data=jsonData)

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
            fullFailure = True
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
