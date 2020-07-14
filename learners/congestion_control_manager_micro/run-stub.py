# Setup the dir
DirOffset = '../../'

import os
import sys
sys.path.insert(0, os.getcwd())
sys.path.insert(0, DirOffset)
import learners.learner_server

if __name__ == '__main__':

    port, address, training = learners.learner_server.parseArgs()

    # EDIT - Define the learner===========================================
    from learners.congestion_control_manager_micro.cc_learner_alt import CCLearner
    learner = CCLearner(training=training)
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