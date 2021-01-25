import time


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

    print('Experimental Run: ~{} hour(s)'.format(testDurationInSeconds/60/60))

    try:

        time.sleep(appNodeServerCooldown)

        networkModule.StartNodes(interNodeDelay=appNodeServerCooldown)

        # Wait for whole test
        time.sleep(testDuration)

    except KeyboardInterrupt as inter:
        keyBoardInterupted = True
    except Exception as ex:
        print(str(ex))
    finally:
        # Stop apps
        print('Stopping Apps')
        networkModule.StopNodes(interNodeDelay=appNodeServerCooldown)
        print('Experiment Done')
        if keyboardInterupRaise and keyBoardInterupted:
            raise KeyboardInterrupt
