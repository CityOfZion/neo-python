# Dockerfile to create images running neo-python
# https://github.com/CityOfZion/neo-python/tree/master/docker
#
# Building an image of the current master branch (creates a Docker image called neopython):
#
#    $ docker build -f Dockerfile -t neopython .
#
# Building an image of the current development branch (creates a Docker image called neopython-dev):
#
#    $ docker build -t neopython-dev . --build-arg branch=development
#
# Build without caching:
#
#    $ docker build --no-cache -f Dockerfile -t neopython .
#
# Using with a private network
# -----------------------------
# If you want to run it connecting to a private network, make sure the privatenet container is already running.
# See also https://hub.docker.com/r/cityofzion/neo-privatenet
#
# Start a container interactively, opening a bash in `/neo-python`, and mounting the current directory as `/neo-python/sc`:
#
#    $ docker run --rm -it -v $(pwd):/neo-python/sc --net=host -h neopython --name neopython neopython /bin/bash
#
# Once you are inside the container, you can start neo-python with `np-prompt` (using -p to connect to a private net).
# To update neo-python, just run `git pull` and `pip install -e .`
FROM alpine

# Branch can be overwritten with --build-arg, eg: `--build-arg branch=development`
ARG branch=master

# Install dependencies

RUN apk --update --virtual=build-dependencies add wget \
    git \
    build-base \
    linux-headers \
    python3 \
    python3-dev \
    libffi-dev \
    py-pip \
    libressl-dev \
    vim \
    man && \
    apk --repository http://dl-3.alpinelinux.org/alpine/edge/testing/ --update add leveldb leveldb-dev && \
    pip3 install --upgrade pip && \
    pip3 install --upgrade setuptools virtualenv cffi


# APT cleanup to reduce image size
RUN rm -rf /var/cache/apk/*

# Clone and setup
RUN git clone https://github.com/CityOfZion/neo-python.git
WORKDIR neo-python
RUN git checkout $branch

# Install the dependencies
RUN pip3 install -e .

# Download the privnet wallet, to have it handy for easy experimenting
RUN wget https://s3.amazonaws.com/neo-experiments/neo-privnet.wallet

# Example run command
CMD /bin/bash
