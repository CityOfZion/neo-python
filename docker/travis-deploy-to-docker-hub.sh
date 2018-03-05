#!/bin/bash
#
# This script is run by Travis CI when a tag is pushed. It creates a Docker image based on
# the current tag, and pushes it to Docker hub: https://hub.docker.com/r/cityofzion/neo-python/
#
REPO=cityofzion/neo-python

# Change into current script directory
cd "$(dirname "$0")"

# Docker: login, build, tag and push
docker login -u $DOCKER_USER -p $DOCKER_PASS
docker build -f Dockerfile -t $REPO:latest . --build-arg branch=$TRAVIS_TAG
docker tag $REPO:latest $REPO:$TRAVIS_TAG
docker push $REPO
