ZooKeeper on Docker
===================

This `Dockerfile` creates a Docker image that can be used as the base for
running ZooKeeper within a Docker container. The ZooKeeper service is ran by
the run.sh script which is in charge of setting up the ZooKeeper configuration
from environment variables passed to the container when it is run.

The version of ZooKeeper is defined in the `Dockerfile` and generally points to
the latest stable release of ZooKeeper.

Environment variables
---------------------

The following environment variables are understood by the startup script to
seed the service's configuration:

  - `ZOOKEEPER_CONFIG_DATA_DIR`, which controls the `dataDir` configuration
    setting. Defaults to `/var/lib/zookeeper`;
  - `ZOOKEEPER_CONFIG_CLIENT_PORT`, which controls the `clientPort`
    configuration setting. Defaults to 2181;
  - `ZOOKEEPER_CONFIG_NODE_ID`, which, when set, determines the node ID in the
    ZooKeeper cluster of this instance. If left empty, the instance assumes it
    is running in single-node mode. Setting this means the node ID will be
    placed in the `$ZOOKEEPER_CONFIG_DATA_DIR/myid` file and the definition of
    the other nodes of the cluster are expected in the
    `ZOOKEEPER_CONFIG_NODE_LIST` environment variable (see below);
  - `ZOOKEEPER_NODE_LIST` is a comma-separated list of `host:port`
    definitions that define, in order, *all* the nodes of the ZooKeeper
    cluster. This information is translated into `server.X=` entries in the
    configuration file. Make sure the node ID used for the instance you start
    matches the hostname (and port) of that corresponding entry in the node
    list.

Usage
-----

To build a new image, simply run from this directory:

```
$ docker build -t `whoami`/zookeeper:3.4.5 .
```

The Docker image will be built and now available in Docker to start a new
container from:

```
$ docker images | grep zookeeper
mpetazzoni/zookeeper   3.4.5              294bef30310b        2 days ago          12.29 kB (virtual 856.7 MB)
```
