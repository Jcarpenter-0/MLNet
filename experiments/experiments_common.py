import time
import subprocess
import requests
import json

LearnersProcs = []
NetworkNodeProcs = []

def runExperiment(NetworkNodes, Learners, Applications, TestingDuration, ServerCool, KillTimeout, dirOffset='./'):
    try:

        # Start Network
        for nodeDef in NetworkNodes:
            NetworkNodeProcs.append(subprocess.Popen(nodeDef))

        print('Network Nodes Setup')

        # Start Learners
        for namePortTrain in Learners:
            learnerDirName = namePortTrain[0]
            modelPort = namePortTrain[1]
            modelMode = namePortTrain[2]
            learnerName = namePortTrain[3]
            modelValidationPattern = namePortTrain[4]
            #learnerAddress = namePortTrain[5]
            LearnersProcs.append(subprocess.Popen(['python3'
                                                      , '{}learners/{}/run-stub.py'.format(dirOffset,learnerDirName)
                                                      , '{}'.format(modelPort)
                                                      , '{}'.format(modelMode)
                                                      , '{}'.format(learnerName)
                                                      , '{}'.format(modelValidationPattern)
                                                      ]))

        print('Learners Setup')

        # Wait for servers to go up
        time.sleep(ServerCool)

        # Start Applications
        for applicationTargetDef in Applications:
            applicationHost = applicationTargetDef[0]
            applicationArgs = applicationTargetDef[1]
            writeDict = {'args': applicationArgs}

            # convert to json
            jsonBody = json.dumps(writeDict).encode()

            # send to the host server to start the application
            response = requests.post(applicationHost + '/processStart/', data=jsonBody)
            print(response)

        # Wait
        time.sleep(TestingDuration)

    except KeyboardInterrupt:
        print('')
    except Exception as ex:
        print('')
    finally:
        # Stop applications
        for applicationTargetDef in Applications:
            applicationHost = applicationTargetDef[0]

            # send to the host server to start the application
            try:
                response = requests.post(applicationHost + '/processStop/')
                print(response)
            except:
                pass

        # Shutdown/Stop experiment
        for learnerProc in LearnersProcs:
            learnerProc.terminate()
            try:
                learnerProc.wait(KillTimeout)
            except Exception as timeout:
                learnerProc.kill()
                learnerProc.wait()

        # Stop Networks
        for networkNode in NetworkNodeProcs:
            networkNode.terminate()
            try:
                networkNode.wait(KillTimeout)
            except Exception as timeout:
                networkNode.kill()
                networkNode.wait()

        print('Experiment Done')