#!/bin/bash

# see http://mininet.org/download/
git clone git://github.com/mininet/mininet

cd mininet
git checkout -b mininet-2.3.0 2.3.0  # or whatever version you wish to install
cd ..

mininet/util/install.sh -a
