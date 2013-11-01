ZooKeeper on Docker
===================

This `Dockerfile` creates a Docker image that can be used as the base for
running ZooKeeper within a Docker container. The run script is responsible for
creating the ZooKeeper configuration based on the container's environment and
starting the ZooKeeper service.

The version of ZooKeeper is defined in the `Dockerfile` and generally points to
the latest stable release of ZooKeeper.

Environment variables
---------------------

The following environment variables are understood by the startup script to
seed the service's configuration:

  - `CONTAINER_NAME` should contain the logical name of the container,
    which will be used for looking up links and ports informations from the
    other environment variables. For this, the name is uppercased and
    non-alphanumeric characters are replaced by underscores.
  - `ZOOKEEPER_<NAME>_CLIENT_PORT`, which controls the `clientPort`
    configuration setting. Defaults to 2181;
  - `ZOOKEEPER_<NAME>_PEER_PORT`, which is used as the peer port specified in
    the server list for this node (and the others). Defaults to 2888;
  - `ZOOKEEPER_<NAME>_LEADER_ELECTION_PORT`, which is used as the leader
    election port specified in the server list for this node (and the others).
    Defaults to 3888.

The ZooKeeper node ID, written out to the `/var/lib/zookeeper/myid` file, is
infered from the position of this container's name in the list of all ZooKeeper
nodes defined in the environment variables. Because these variables are always
looked at in sorted order, this is deterministic as long as all ZooKeeper node
containers start with the same set of `ZOOKEEPER_*` environment variables.

Volumes
-------

The ZooKeeper images uses the following volumes that you may want to bind from
the container's host:

  - `/var/lib/zookeeper`, for the ZooKeeper data snapshots.

Usage
-----

To build a new image, simply run from this directory:

```
$ docker build -t `whoami`/zookeeper:3.4.5 .
```

The Docker image will be built and now available for Docker to start a new
container from:

```
$ docker images | grep zookeeper
mpetazzoni/zookeeper   3.4.5              294bef30310b        2 days ago          12.29 kB (virtual 856.7 MB)
```
