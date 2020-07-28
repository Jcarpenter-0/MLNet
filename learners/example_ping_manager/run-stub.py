import pandas as pd

# Setup the dir
DirOffset = '../../'

import os
import sys
sys.path.insert(0, os.getcwd())
sys.path.insert(0, DirOffset)
import learners.learner_server

if __name__ == '__main__':

    port, address, mode, name, validationFilePath, traceFilePrefix = learners.learner_server.parseArgs()

    validationPatternDF = None

    if name is None:
        raise Exception('Need learner name')

    if mode == 2 and validationFilePath is not None:
        validationPatternDF = pd.read_csv(validationFilePath)

    elif mode == 2 and validationFilePath is None:
        raise Exception('Need validation file path for validation mode')


    # EDIT - Define the learner===========================================
    from learners.example_ping_manager.example_ping_manager import Learner
    learner = Learner(learnerMode=mode, learnerName=name, validationPattern=validationPatternDF, traceFilePrefix=traceFilePrefix)
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