#!/bin/sh
export GITROOT=https://:@gitlab.cern.ch:8443/frontier
dir=/tmp/rpms
mkdir -p $dir
cd $dir
packages="doc frontier-release frontier-tomcat scripts"
for package in $packages; do
    git clone $GITROOT/rpms/$package.git
done
