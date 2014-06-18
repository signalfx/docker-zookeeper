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

# First, gather ZooKeeper nodes from the environment.
ZOOKEEPER_NODE_LIST = get_node_list(get_service_name(),
                                    ports=['peer', 'leader_election'])

# Build a representation of ourselves, to match against the node list.
myself = '{}:{}:{}'.format(
    get_specific_host(get_service_name(), get_container_name()),
    get_specific_port(get_service_name(), get_container_name(), 'peer'),
    get_specific_port(get_service_name(), get_container_name(),
                      'leader_election'))

# Build the ZooKeeper node configuration.
conf = {
    'tickTime': 2000,
    'initLimit': 10,
    'syncLimit': 5,
    'dataDir': ZOOKEEPER_DATA_DIR,
    'clientPort': get_port('client', 2181),
}

# Add the ZooKeeper node list with peer and leader election ports.
for id, node in enumerate(ZOOKEEPER_NODE_LIST, 1):
    conf['server.{}'.format(id)] = node
    # Make a note of our node ID if we find ourselves in the list.
    if node == myself:
        ZOOKEEPER_NODE_ID = id

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

# Write out the 'myid' file in the data directory if we found ourselves in the
# node list.
if ZOOKEEPER_NODE_ID:
    if not os.path.exists(ZOOKEEPER_DATA_DIR):
        os.makedirs(ZOOKEEPER_DATA_DIR, mode=0750)
    with open(os.path.join(ZOOKEEPER_DATA_DIR, 'myid'), 'w+') as f:
        f.write('%s\n' % ZOOKEEPER_NODE_ID)
    print('Starting {}, node {} of a {}-node ZooKeeper cluster...'.format(
        get_container_name(),
        ZOOKEEPER_NODE_ID,
        len(ZOOKEEPER_NODE_LIST)))
else:
    print('Starting {} as a single-node ZooKeeper cluster...'.format(
        get_container_name()))

jvm_flags = ['-server', '-showversion']
jmx_port = get_port('jmx', -1)
if jmx_port != -1:
    jvm_flags.extend([
        '-Djava.rmi.server.hostname={}'.format(get_container_host_address()),
        '-Dcom.sun.management.jmxremote.port={}'.format(jmx_port),
        '-Dcom.sun.management.jmxremote.rmi.port={}'.format(jmx_port),
        '-Dcom.sun.management.jmxremote.local.only=false',
        '-Dcom.sun.management.jmxremote.authenticate=false',
        '-Dcom.sun.management.jmxremote.ssl=false',
    ])

jvm_flags.append('-Dvisualvm.display.name="{}/{}"'.format(
    get_environment_name(), get_container_name()))

os.environ['JVMFLAGS'] = ' '.join(jvm_flags) + os.environ.get('JVM_OPTS', '')

sys.stderr.write('Using JVM_FLAGS: {}\n'.format(jvm_flags))

# Start ZooKeeper
os.execl('bin/zkServer.sh', 'zookeeper', 'start-foreground')
