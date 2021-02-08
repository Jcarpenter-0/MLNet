import time
import datetime


def runExperimentUsingFramework(networkModule, testDuration:int, appNodeServerCooldown:int=5, keyboardInterupRaise:bool=True):
    """
        Outline assumptions here:
        -Daemon server on hosts
        -Network already setup with nodes setup (running daemon servers)

    :param networkModule:
    :param testDuration:
    :param killTimeout:
    :param keyboardInterupRaise:
    """

    keyBoardInterupted = False

    # calulate meta info
    testDurationInSeconds = testDuration + (len(networkModule.Nodes) * appNodeServerCooldown)

    print('Test: ~{} hour(s)'.format(testDurationInSeconds/60/60))

    try:
        setupStart = datetime.datetime.now()
        print('Test: Setup started: {}'.format(setupStart))
        time.sleep(appNodeServerCooldown)

        networkModule.StartNodes(interNodeDelay=appNodeServerCooldown)

        testBegin = datetime.datetime.now()
        print('Test: Setup complete: {} | Setup delay(ms) {}'.format(testBegin, (testBegin - setupStart).seconds * 1000))

        # Wait for whole test
        time.sleep(testDuration)

    except KeyboardInterrupt as inter:
        keyBoardInterupted = True
    except Exception as ex:
        print(str(ex))
    finally:
        # Stop Applications on the nodes
        networkModule.StopNodes(interNodeDelay=appNodeServerCooldown)

        print('Test Complete {}'.format(datetime.datetime.now()))
        if keyboardInterupRaise and keyBoardInterupted:
            raise KeyboardInterrupt
