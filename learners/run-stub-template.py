# Setup the dir
DirOffset = '../../'

import os
import sys
sys.path.insert(0, os.getcwd())
sys.path.insert(0, DirOffset)
import learners.learner_server

if __name__ == '__main__':

    port, address, mode, name, validationFilePath = learners.learner_server.parseArgs()

    validationPattern = None

    if name is None:
        raise Exception('Need learner name')

    if mode == 2 and validationFilePath is not None:
        validationFileDS = open(validationFilePath, 'r')

        validationPattern = validationFileDS.readlines()
    elif mode == 2 and validationFilePath is None:
        raise Exception('Need validation file path for validation mode')


    # EDIT - Define the learner===========================================
    from learners.congestion_control_manager_micro.cc_learner import CCLearner
    learner = CCLearner(learnerMode=mode, learnerName=name, validationPattern=validationPattern)
    # ====================================================================

    learners.learner_server.DefineLearner(learner)

    webserver = learners.learner_server.OperationServer(address, port)

    try:
        webserver.run()
    except KeyboardInterrupt:
        print()
    except Exception as ex:
        print()
    finally:
        webserver.cleanup()