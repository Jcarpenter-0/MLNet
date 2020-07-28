#!/usr/bin/env bash

# Helpful link: https://tech.amikelive.com/node-887/how-to-resolve-error-illegal-instruction-core-dumped-when-running-import-tensorflow-in-a-python-program/

#sudo apt-get update
#sudo apt-get -y install python3-pip

# install old keras
pip3 install keras
# older version ==2.1.5
# sudo pip install [package_name] --upgrade
# sudo pip uninstall [package_name]

# install older tensorflow, due to older cpu's lacking AVX support
pip3 install tensorflow
# ==1.5

# To check for AVX support
#more /proc/cpuinfo | grep flags

# install sklearn
pip3 install sklearn

# install pandas
pip3 install pandas
