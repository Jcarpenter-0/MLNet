#!/usr/bin/env bash
sh 01-setup-congestion-controls.sh

sh 02-setup-mahi-mahi.sh

python3 experiment_02_2_nodes.py
