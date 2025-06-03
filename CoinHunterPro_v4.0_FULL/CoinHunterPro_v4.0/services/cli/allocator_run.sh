#!/bin/bash

cd /home/ubuntu/CoinHunterV4/CoinHunterPro_v4.0_FULL/CoinHunterPro_v4.0/services/cli
source ../../venv/bin/activate
PYTHONPATH=../.. python capital_allocator_cli.py --capital 10000000 --threshold 0.05
