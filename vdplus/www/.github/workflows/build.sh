#!/usr/bin/env bash
set -e

# Build the VisiData Docker image
pushd vd
docker build -t vdwww .
popd

# Build the VisiData Hub Docker image
pushd hub
docker build -t vdhub .
popd

