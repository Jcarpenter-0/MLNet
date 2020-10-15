#!/usr/bin/env bash

# Helpful link: https://tech.amikelive.com/node-887/how-to-resolve-error-illegal-instruction-core-dumped-when-running-import-tensorflow-in-a-python-program/

#sudo apt-get update
#sudo apt-get -y install python3-pip
# Update pip
# pip install --upgrade pip

# Install pip3
sudo apt install python3-pip
pip3 install --upgrade pip3

# Install tensorflow
pip3 install tensorflow
# install older tensorflow, due to older cpu's lacking AVX support
# ==1.5

# Install keras
pip3 install keras
# older version ==2.1.5
# sudo pip install [package_name] --upgrade
# sudo pip uninstall [package_name]

# To check for AVX support
#more /proc/cpuinfo | grep flags

# Install sklearn
pip3 install sklearn

# Install pandas
pip3 install pandas
