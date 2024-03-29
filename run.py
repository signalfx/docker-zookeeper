#!/usr/bin/env python

# Copyright (C) 2013 SignalFuse, Inc.

# Start script for the ZooKeeper service.
# Because of the nature of the bootstrapping of the ZooKeeper cluster, we make
# use of some "internal" Maestro guest helper functions here.

from __future__ import print_function

import os
import sys

from signalfx_orchestration_utils import get_container_name, \
    get_service_name, get_port, get_specific_host, get_specific_port, \
    get_environment_name, get_node_list, get_container_host_address

os.chdir(os.path.join(
    os.path.dirname(os.path.abspath(__file__)),
    '..'))

CONTAINER_NAME = get_container_name()
ZOOCFGDIR = os.environ.get('ZOOCFGDIR', 'conf')
ZOOKEEPER_CONFIG_FILE = os.path.join(ZOOCFGDIR, 'zoo.cfg')
ZOOKEEPER_DYNAMIC_CONFIG_FILE = os.path.join(ZOOCFGDIR, 'zoo.cfg.dynamic')
ZOOKEEPER_LOG_CONFIG_FILE = os.path.join(ZOOCFGDIR, 'log4j.properties')
RECONFIG_ENABLED = (os.environ.get('RECONFIG_ENABLED', "").lower() == 'true')
ZOOKEEPER_DATA_DIR = os.environ.get('ZK_DATA_DIR', '/var/lib/zookeeper')
ZOOKEEPER_NODE_ID = None
SERVICE_NAME = get_service_name()
DISCOVERY_SERVICE_NAME = os.environ.get('DISCOVERY_SERVICE_NAME', SERVICE_NAME)
LOG_DIR = os.environ.get('LOG_DIR', '/var/log/{}'.format(SERVICE_NAME))

LOG_PATTERN = (
    "%d{yyyy'-'MM'-'dd'T'HH:mm:ss.SSSXXX} %-5p [%-35.35t] [%-36.36c]: %m%n")

RMI_ENABLED = os.environ.get('RMI_ENABLED', 'true')
RMI_LOCAL_HOST = os.environ.get('RMI_LOCAL_HOST', 'true')

# Build the ZooKeeper node configuration.
conf = {
    'tickTime': 2000,
    'initLimit': 10,
    'syncLimit': 5,
    '4lw.commands.whitelist': '*',
    'admin.enableServer': 'false',
    'reconfigEnabled': 'true' if RECONFIG_ENABLED else 'false',
    'dataDir': ZOOKEEPER_DATA_DIR,
    'quorumListenOnAllIPs': True,
    'clientPort': get_port('client', 2181),
    'autopurge.snapRetainCount':
        int(os.environ.get('MAX_SNAPSHOT_RETAIN_COUNT', 10)),
    'autopurge.purgeInterval':
        int(os.environ.get('PURGE_INTERVAL', 24)),
    'maxClientCnxns':
        int(os.environ.get('MAX_CLIENT_CONNECTIONS', 60)),
    'globalOutstandingLimit':
        int(os.environ.get('GLOBAL_OUTSTANDING_LIMIT', 1000)),
}
dynamic_conf = {}


def build_node_repr(name):
    """Build the representation of a node with peer and leader-election
    ports."""
    peer = get_specific_port(DISCOVERY_SERVICE_NAME, name, 'peer')
    election = get_specific_port(DISCOVERY_SERVICE_NAME, name, 'leader_election') or get_specific_port(DISCOVERY_SERVICE_NAME, name, 'election')
    client = get_specific_port(DISCOVERY_SERVICE_NAME, name, 'client', 2181)
    node_repr = '{}:{}:{}:participant;{}'.format(
        get_specific_host(DISCOVERY_SERVICE_NAME, name), peer, election, client)

    if (not peer) or (not election) or (not client):
        print('Failed to build node representation: %s' % node_repr)
        sys.exit(1)
    return node_repr


# Add the ZooKeeper node list with peer and leader election ports and figure
# out our own ID. ZOOKEEPER_SERVER_IDS contains a comma-separated list of
# node:id tuples describing the server ID of each node in the cluster, by its
# container name. If not specified, we assume single-node mode.
if os.environ.get('ZOOKEEPER_SERVER_IDS'):
    servers = os.environ['ZOOKEEPER_SERVER_IDS'].split(',')
    for server in servers:
        node, server_id = server.split(':')
        dynamic_conf['server.{}'.format(server_id)] = build_node_repr(node)
        if node == CONTAINER_NAME:
            ZOOKEEPER_NODE_ID = server_id

ZOOKEEPER_ADDITIONAL_NODE_COUNT = 0
if os.environ.get('ZOOKEEPER_ADDITIONAL_SERVERS'):
    servers = os.environ['ZOOKEEPER_ADDITIONAL_SERVERS'].split(',')
    ZOOKEEPER_ADDITIONAL_NODE_COUNT = len(servers)
    for server in servers:
        server_id, node_repr = server.split('=')
        dynamic_conf[server_id] = node_repr

# Verify that the number of declared nodes matches the size of the cluster.
ZOOKEEPER_NODE_COUNT = os.environ.get('ZK_REPLICAS') or (len(get_node_list(DISCOVERY_SERVICE_NAME)) + ZOOKEEPER_ADDITIONAL_NODE_COUNT)
ZOOKEEPER_NODE_COUNT = int(ZOOKEEPER_NODE_COUNT)
ZOOKEEPER_CLUSTER_SIZE = len(
    [i for i in dynamic_conf.keys() if i.startswith('server.')])

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
    print(('Mismatched number of nodes between ' +
           'ZOOKEEPER_SERVER_IDS ({}) and the declared ' +
           'cluster ({})!\n')
          .format(ZOOKEEPER_CLUSTER_SIZE), ZOOKEEPER_NODE_COUNT)
    sys.exit(1)

# Write out the ZooKeeper configuration files.
static_conf = conf.copy()
if RECONFIG_ENABLED:
    # ZK creates new dynamic config file every time reconfiguration happens.
    # We need to find out which one was used most recently.
    cur_dynamic_config = None
    if os.path.exists(ZOOKEEPER_CONFIG_FILE):
        with open(ZOOKEEPER_CONFIG_FILE, 'r') as f:
            for l in f.readlines():
                k, v = l.strip().split("=")
                if k == 'dynamicConfigFile':
                    cur_dynamic_config = v
                    break
    static_conf['dynamicConfigFile'] = cur_dynamic_config or ZOOKEEPER_DYNAMIC_CONFIG_FILE

    if cur_dynamic_config:
        print('Using pre-existent dynamic config file %s.' % cur_dynamic_config)
    elif os.path.exists(ZOOKEEPER_DYNAMIC_CONFIG_FILE):
        print('Dynamic config file already exists at %s.' % ZOOKEEPER_DYNAMIC_CONFIG_FILE)
    else:
        with open(ZOOKEEPER_DYNAMIC_CONFIG_FILE, 'w+') as f:
            for entry in sorted(dynamic_conf.iteritems()):
                f.write("%s=%s\n" % entry)
        print('Written new dynamic config file at %s.' % ZOOKEEPER_DYNAMIC_CONFIG_FILE)
else:
    static_conf.update(dynamic_conf)
with open(ZOOKEEPER_CONFIG_FILE, 'w+') as f:
    for entry in sorted(static_conf.iteritems()):
        f.write("%s=%s\n" % entry)

# Setup the logging configuration.
zk_root_logger = 'log4j.rootLogger=' + os.environ.get('LOG_LEVEL', 'INFO')
log_conf = ''
if os.environ.get('LOG_TO_STDOUT', 'false').lower() == 'true':
    zk_root_logger += ', stdout'
    log_conf += """# Log4j config, logs to stdout
log4j.appender.stdout=org.apache.log4j.ConsoleAppender
log4j.appender.stdout.layout=org.apache.log4j.PatternLayout
log4j.appender.stdout.layout.ConversionPattern=%s
""" % LOG_PATTERN

elif True:
    # TODO: replace with following condition after we're fully migrated to k8s:
    # if os.environ.get('LOG_TO_FILE', 'true').lower() == 'true':
    zk_root_logger += ', R'
    log_conf += """# Log4j configuration, logs to rotating file
log4j.appender.R=org.apache.log4j.RollingFileAppender
log4j.appender.R.File=%s
log4j.appender.R.MaxFileSize=100MB
log4j.appender.R.MaxBackupIndex=10
log4j.appender.R.layout=org.apache.log4j.PatternLayout
log4j.appender.R.layout.ConversionPattern=%s
""" % (os.path.join(LOG_DIR, CONTAINER_NAME + '.log'), LOG_PATTERN)

log_conf = zk_root_logger + '\n' + log_conf
with open(ZOOKEEPER_LOG_CONFIG_FILE, 'w+') as log_file:
    log_file.write(log_conf)

# Write out the 'myid' file in the data directory if in cluster mode.
if ZOOKEEPER_NODE_ID:
    if not os.path.exists(ZOOKEEPER_DATA_DIR):
        os.makedirs(ZOOKEEPER_DATA_DIR, mode=0750)
    with open(os.path.join(ZOOKEEPER_DATA_DIR, 'myid'), 'w+') as f:
        f.write('%s\n' % ZOOKEEPER_NODE_ID)
    print('Starting {}, node id#{} of a {}-node ZooKeeper cluster...\n'
          .format(CONTAINER_NAME, ZOOKEEPER_NODE_ID, ZOOKEEPER_CLUSTER_SIZE))
else:
    print('Starting {} as a single-node ZooKeeper cluster...\n'
          .format(CONTAINER_NAME))

jvmflags = [
    '-server',
    '-showversion',
    '-Dznode.container.checkIntervalMs={}'.format(int(os.environ.get('CONTAINER_MANAGER_CHECK_INTERVAL_MS', 60000))),
    '-Dznode.container.maxPerMinute={}'.format(int(os.environ.get('CONTAINER_MANAGER_MAX_PER_MIN', 10000))),
    '-Dvisualvm.display.name="{}/{}"'.format(
        get_environment_name(), CONTAINER_NAME),
]

jmx_port = get_specific_port(DISCOVERY_SERVICE_NAME, CONTAINER_NAME, 'jmx', -1)
if jmx_port != -1:
    jvmflags += [
        '-Djava.rmi.server.hostname={}'.format(get_container_host_address()),
        '-Dcom.sun.management.jmxremote.port={}'.format(jmx_port),
        '-Dcom.sun.management.jmxremote.authenticate=false',
        '-Dcom.sun.management.jmxremote.local.only=false',
        '-Dcom.sun.management.jmxremote.ssl=false',
    ]
    if RMI_ENABLED.lower() == 'true':
        rmi_port = get_specific_port(DISCOVERY_SERVICE_NAME, CONTAINER_NAME, 'rmi', jmx_port)
        if RMI_LOCAL_HOST.lower() == 'true':
            rmi_server = 'localhost'
        else:
            rmi_server = get_container_host_address()
        if rmi_port != -1:
            jvmflags += [
                '-Djava.rmi.server.hostname={}'.format(rmi_server),
                '-Dcom.sun.management.jmxremote.rmi.port={}'.format(rmi_port),
            ]


os.environ['JVMFLAGS'] = ' '.join(jvmflags) + ' ' + os.environ.get('JVM_OPTS', '')

# Start ZooKeeper
os.execl('bin/zkServer.sh', 'zookeeper', 'start-foreground')
