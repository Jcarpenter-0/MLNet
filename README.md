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

* See applications directory readme for application specific information

* See experiments directory readme for how to setup tests

* See learners directory readme for how to run and setup learners

* See networks directory readme for how to use network sims