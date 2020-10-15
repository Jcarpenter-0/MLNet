# Learners
This project includes a few learners with the system as examples, patterns, and initial functionality:
* example_ping_manager
* congestion_control_manager

These examples utilize the Keras (tensorflow) library, and use multiple models to predict multiple values.

## Creating a Learner
Learners are organized into their own directories (eg: ./learners/example_ping_manager/). From these directories is a <i>run-stub.py</i> and <i>learner.py</i> file.
<i>run-stub.py</i> handles actually running the learner (see Running Learner Server section) and <i>learner.py</i> defines the learner's reward, action space, input space, etc.

To create:
* make a new directory ./learners/\<learnername\>/
* create a learner definition file (learner.py for example), inherit a suitable learner base class from 
<i>learner_common.py</i>
* copy paste <i>run-stub.py</i> from another project and change the lines defining the learner:

<code>from learners.congestion_control_manager_micro.cc_learner import CCLearner</code>

<code>learner = CCLearner(learnerMode=mode, learnerName=name, validationPattern=validationPatternDF, traceFilePrefix=traceFilePrefix)</code>

## Running Learner Server
Inside each of the learner sub directories is a <i>run-stub.py</i> file. Running this will create that specific learner and setup the server for coordinating it with incoming data and outgoing action suggestions.

<code>python3 run-stub.py \<port\> \<address\> \<learnerMode\> \<learnerLabel\> \<tracefileLabel\> \<validationPatternFilePath\>  </code>

* To start a learner in training mode:

<code>python3 run-stub.py 8080 "" 1 "Training-Learner" "" ""</code>

* To start a learner in testing mode (apply model, not expand it):

<code>python3 run-stub.py 8080 "" 0 "Testing-Learner" "" ""</code>

* To start a learner in validation mode (no learner-action just provide actions following a pattern and collect traces)

<code>python3 run-stub.py 8080 "" 2 "Validating-Learner" "" "pattern-file.csv"</code>

* With the server running, you can check the status via <url>http://localhost:8080/<url>

* To submit data to the model, use POST requests with parameters matching the expected inputs of the learner

# Troubleshooting
* Illegal operation (core dumped)
Check tensorflow, it may be running a new version on an older cpu
* Shape input issues? Try ensuring that keras and tensorflow are updated properly

# Tips for doing Machine Learning
* Use only numeric data, text will not translate properly, use a mapping to either numeric values or binary columns to address
* Consider using data that is "relevant" to achieving an end, this is a heuristic