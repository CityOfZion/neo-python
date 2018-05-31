This directory contains various Docker related utilities.

* `Dockerfile.master` -- a Dockerfile to build neo-python's master branch
* `Dockerfile.dev` -- a Dockerfile to build neo-python's development branch
* `docker-compose-neoscan.yml` -- a Docker compose file to start a private network and a neoscan container

---

## Simple Docker container for neo-python master and dev branches

Take a look at the Dockerfile, it has some documentation and example usage inside.

Building an image of the current master branch (creates a Docker image called neopython):

    $ docker build -f Dockerfile -t neopython .

Building an image of the current development branch (creates a Docker image called neopython-dev):

    $ docker build -f Dockerfile -t neopython-dev . --build-arg branch=development

Build without caching:

    $ docker build --no-cache -f Dockerfile -t neopython .

### Using with a private network

If you want to run it connecting to a private network, make sure the privatenet container is already running.
See also https://hub.docker.com/r/cityofzion/neo-privatenet

Start a container interactively, opening a bash in `/neo-python`, and mounting the current directory as `/neo-python/sc`:

    $ docker run --rm -it -v $(pwd):/neo-python/sc --net=host -h neopython --name neopython neopython /bin/bash

Once you are inside the container, you can start neo-python with `np-prompt -p` (using -p to connect to a private net).
To update neo-python, just run `git pull` and `pip install -e .`

## NeoScan and the private network

`docker-compose-neoscan.yml` sets you up with 2 Docker containers: one for the private network and one for neoscan connected to it.
The base project and neoscan Dockerfile is currently maintained here: https://github.com/slipo/neo-scan-docker

You can start the privatenet+neoscan combo with this command:

    $ docker-compose -f docker-compose-neoscan.yml up

It will take some time to set up.

While you wait, add this line to your hosts file:

    127.0.0.1 neo-privnet

That allows you to connect to the privnet NEO nodes with the URLs returned by the neo-scan container. If you're using neo-python to connect to the privnet, you can use the standard configuration. 127.0.0.1:30333 will continue to work, for example.

OK, if you waited a few minutes, it should be ready. Check: http://localhost:4000/. You should see neo-scan with some blocks.
