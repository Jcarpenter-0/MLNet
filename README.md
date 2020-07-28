# MLNet
Networking-oriented machine learning platform
* Modular RL systems
    * Learner Server - Provides GET/POST support for POSTing learner data and responding with a recommended action ID.
    * Application Server - runs applications remotely, not secure, just for running apps
* Basic Testing Framework

# Installation
* FOR UBUNTU 18.04+
* Setup Keras, tensorflow, and sklearn by running the setupkeras.sh script

# Running Standalone modules
Each component of the framework is standalone running from HTTP Web servers with a REST-like type microservice structure.
GET will provide information about a module to a requester and POST will handle operations (learning/action requesting for users and application management for testing).
* Run the Learner Module by running the "run-stub.py [port to listen on] [0 or 1 for not training and training]" for a specific model under the directory "learners/"
* Run the Operation Module by running the "operation_server.py [port to listen on]" in "applications/". Then POST command line args to the server to run/manage host applications.

# Running Using the Basic Framework
A basic framework is provided that provides a space to setup experimental parameters via python script.

* Example in "experiments/example_01_example/experiment_01_example.py"

# Building a Learner
* Create a new folder in learners/ and add two python files (a copy of run-stub.py modified to import the proper RL you wish to use and a file that inhereits the RL core from learner_common.py)
* In the new copy of inheritence file, define a reward from the state you expect (as a python dict, you select the textual field labels you wish to use)
* Modify the construction of the RL class to fit particular hyper parameters you desire (layers, epochs, etc)

# Tips for doing Machine Learning
* Use only numeric data, text will not translate properly, use a mapping to either numeric values or binary columns to address
* Consider using data that is "relevant" to achieving an end, this is a heuristic