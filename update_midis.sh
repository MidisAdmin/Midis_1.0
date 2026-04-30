#!/bin/bash
cd ~/Midis_1.0
git pull
cp *.py ~/
sudo systemctl restart midis
