#!/bin/bash

# Download installer
wget -O '~/sprinkle/tmp/miniconda-installer.sh' 'https://repo.anaconda.com/miniconda/Miniconda3-latest-Linux-x86_64.sh'
# Execute installer
chmod u+x '~/sprinkle/tmp/miniconda-installer.sh'
source ~/sprinkle/tmp/miniconda-installer.sh -f -b -p ~/miniconda
# Clean up installer
rm -f ~/sprinkle/tmp/miniconda-installer.sh

# Integrate and setup miniconda
eval "$($HOME/miniconda/bin/conda shell.bash hook)"
source ~/.bashrc
conda init
conda config --set auto_activate_base false
