#!/usr/bin/env python

# Copyright (C) 2013 SignalFuse, Inc.

# Start script for the ZooKeeper service.
# Because of the nature of the bootstrapping of the ZooKeeper cluster, we make
# use of some "internal" Maestro guest helper functions here.

from __future__ import print_function

import os
import sys

from maestro.guestutils import (
    get_container_name, get_node_list, get_service_name, get_port,
    get_specific_host, get_specific_port, get_container_host_address,
    get_environment_name)


os.chdir(os.path.join(
    os.path.dirname(os.path.abspath(__file__)),
    '..'))

ZOOKEEPER_CONFIG_FILE = os.path.join('conf', 'zoo.cfg')
ZOOKEEPER_LOG_CONFIG_FILE = os.path.join('conf', 'log4j.properties')
ZOOKEEPER_DATA_DIR = '/var/lib/zookeeper'
ZOOKEEPER_NODE_ID = None

LOG_PATTERN = (
    "%d{yyyy'-'MM'-'dd'T'HH:mm:ss.SSSXXX} %-5p [%-35.35t] [%-36.36c]: %m%n")

# Build the ZooKeeper node configuration.
conf = {
    'tickTime': 2000,
    'initLimit': 10,
    'syncLimit': 5,
    'dataDir': ZOOKEEPER_DATA_DIR,
    'clientPort': get_port('client', 2181),
    'quorumListenOnAllIPs': True,
    'autopurge.snapRetainCount':
        int(os.environ.get('MAX_SNAPSHOT_RETAIN_COUNT', 10)),
    'autopurge.purgeInterval':
        int(os.environ.get('PURGE_INTERVAL', 24)),
}


def build_node_repr(name):
    """Build the representation of a node with peer and leader-election
    ports."""
    return '{}:{}:{}'.format(
        get_specific_host(get_service_name(), name),
        get_specific_port(get_service_name(), name, 'peer'),
        get_specific_port(get_service_name(), name, 'leader_election'))


# Add the ZooKeeper node list with peer and leader election ports and figure
# out our own ID. ZOOKEEPER_SERVER_IDS contains a comma-separated list of
# node:id tuples describing the server ID of each node in the cluster, by its
# container name. If not specified, we assume single-node mode.
if os.environ.get('ZOOKEEPER_SERVER_IDS'):
    servers = os.environ['ZOOKEEPER_SERVER_IDS'].split(',')
    for server in servers:
        node, id = server.split(':')
        conf['server.{}'.format(id)] = build_node_repr(node)
        if node == get_container_name():
            ZOOKEEPER_NODE_ID = id

# Verify that the number of declared nodes matches the size of the cluster.
ZOOKEEPER_NODE_COUNT = len(get_node_list(get_service_name()))
ZOOKEEPER_CLUSTER_SIZE = len(
    [i for i in conf.keys() if i.startswith('server.')])

# If no ZOOKEEPER_SERVER_IDS is defined, we expect to be in single-node mode so
# no more than one node can be declared in the cluster.
if ZOOKEEPER_CLUSTER_SIZE == 0 and ZOOKEEPER_NODE_COUNT != 1:
    sys.stderr.write(('Missing ZOOKEEPER_SERVER_IDS declaration for ' +
                      '{}-node ZooKeeper cluster!\n')
                     .format(ZOOKEEPER_NODE_COUNT))
    sys.exit(1)

# If we got nodes from ZOOKEEPER_SERVER_IDS, we expect exactly the same number
# of nodes declared in the cluster.
if ZOOKEEPER_CLUSTER_SIZE > 0 and \
        ZOOKEEPER_CLUSTER_SIZE != ZOOKEEPER_NODE_COUNT:
    sys.stderr.write(('Mismatched number of nodes between ' +
                      'ZOOKEEPER_SERVER_IDS ({}) and the declared ' +
                      'cluster ({})!\n')
                     .format(ZOOKEEPER_CLUSTER_SIZE), ZOOKEEPER_NODE_COUNT)
    sys.exit(1)

# Write out the ZooKeeper configuration file.
with open(ZOOKEEPER_CONFIG_FILE, 'w+') as f:
    for entry in conf.iteritems():
        f.write("%s=%s\n" % entry)

# Setup the logging configuration.
with open(ZOOKEEPER_LOG_CONFIG_FILE, 'w+') as f:
    f.write("""# Log4j configuration, logs to rotating file
log4j.rootLogger=INFO,R

log4j.appender.R=org.apache.log4j.RollingFileAppender
log4j.appender.R.File=/var/log/%s/%s.log
log4j.appender.R.MaxFileSize=100MB
log4j.appender.R.MaxBackupIndex=10
log4j.appender.R.layout=org.apache.log4j.PatternLayout
log4j.appender.R.layout.ConversionPattern=%s
""" % (get_service_name(), get_container_name(), LOG_PATTERN))

# Write out the 'myid' file in the data directory if in cluster mode.
if ZOOKEEPER_NODE_ID:
    if not os.path.exists(ZOOKEEPER_DATA_DIR):
        os.makedirs(ZOOKEEPER_DATA_DIR, mode=0750)
    with open(os.path.join(ZOOKEEPER_DATA_DIR, 'myid'), 'w+') as f:
        f.write('%s\n' % ZOOKEEPER_NODE_ID)
    sys.stderr.write(
        'Starting {}, node id#{} of a {}-node ZooKeeper cluster...\n'
        .format(get_container_name(), ZOOKEEPER_NODE_ID,
                ZOOKEEPER_CLUSTER_SIZE))
else:
    sys.stderr.write('Starting {} as a single-node ZooKeeper cluster...\n'
                     .format(get_container_name()))

jvmflags = [
    '-server',
    '-showversion',
    '-Dvisualvm.display.name="{}/{}"'.format(
        get_environment_name(), get_container_name()),
]

jmx_port = get_port('jmx', -1)
if jmx_port != -1:
    jvmflags += [
        '-Djava.rmi.server.hostname={}'.format(get_container_host_address()),
        '-Dcom.sun.management.jmxremote.port={}'.format(jmx_port),
        '-Dcom.sun.management.jmxremote.rmi.port={}'.format(jmx_port),
        '-Dcom.sun.management.jmxremote.authenticate=false',
        '-Dcom.sun.management.jmxremote.local.only=false',
        '-Dcom.sun.management.jmxremote.ssl=false',
    ]

os.environ['JVMFLAGS'] = ' '.join(jvmflags) + ' ' + os.environ.get('JVM_OPTS', '')

# Start ZooKeeper
os.execl('bin/zkServer.sh', 'zookeeper', 'start-foreground')
