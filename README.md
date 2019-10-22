# MLNet
Networking-oriented machine learning platform


# System Structure
[Client <-> Network <-> Server] <=> Learner

Broadly this platform is comprised of 4 parts: A client application that runs *inside* the network application (simulated or real) that interacts with a server application. All of these components report to a Machine Learning (Learner) application that then examines the reports and provides a action/modification to those components who in turn repeat the process. Together this creates a feedback loop that follows the basic definition of Reinforcement Learning based Machine Learning.

# Installation
1. Ensure python3, matplotlib, pandas, and keras

# Adding a Learner (RL)
1. Create a new python directory inside /Learners with the name of the learner you wish to make (ex: Bandwidth Throttler).
2. Copy paste and rename /Learners/rlTemplate.py into this new folder (ex: BandwidthThrottler.py)
3. Fill in the "EDITABLE -" annotated methods with logic you wish to utilize () 

# Adding a Client
1. Create a new python directory inside /Client
2. Copy paste and rename /Client/clientTemplate.py into the new directory
3.

# Adding a Server
1.
2.
3.

# Adding a Network
1.
2.
3.