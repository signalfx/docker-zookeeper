#!/usr/bin/env python
"""
Startup script for the ZooKeeper service.
"""

from __future__ import print_function
import os
import sys

from signalfx_orchestration_utils import *

os.chdir(os.path.join(
    os.path.dirname(os.path.abspath(__file__)),
    '..'))

CONTAINER_NAME = get_container_name()
ZOOKEEPER_CONFIG_FILE = os.path.join('conf', 'zoo.cfg')
ZOOKEEPER_LOG_CONFIG_FILE = os.path.join('conf', 'log4j.properties')
ZOOKEEPER_DATA_DIR = os.environ.get('ZK_DATA_DIR', '/var/lib/zookeeper')
ZOOKEEPER_NODE_ID = None
SERVICE_NAME = get_service_name()
DISCOVERY_SERVICE_NAME = os.environ.get('DISCOVERY_SERVICE_NAME', SERVICE_NAME)
LOG_DIR = os.environ.get('LOG_DIR',
                         '/var/log/{}'.format(SERVICE_NAME))
LOG_PATTERN = (
    "%d{yyyy'-'MM'-'dd'T'HH:mm:ss.SSSXXX} %-5p [%-35.35t] [%-36.36c]: %m%n")

def build_node_repr(name):
    """Build the representation of a node with peer and leader-election
    ports."""
    return '{}:{}:{}:participant;{}'.format(
        get_specific_host(DISCOVERY_SERVICE_NAME, name),
        get_specific_port(DISCOVERY_SERVICE_NAME, name, 'peer'),
        get_specific_port(DISCOVERY_SERVICE_NAME, name, 'election'),
        get_specific_port(DISCOVERY_SERVICE_NAME, name, 'client'),
    )

# Build and write the ZooKeeper node configuration.
conf = {
    'tickTime': int(os.environ.get('ZK_TICK_TIME', 2000)),
    'initLimit': int(os.environ.get('ZK_INIT_TIME', 10)),
    'syncLimit': int(os.environ.get('ZK_SYNC_LIMIT', 5)),
    '4lw.commands.whitelist': '*',
    'admin.enableServer': 'false',
    'reconfigEnabled': os.environ.get('RECONFIG_ENABLED', "false"),
    'skipACL': os.environ.get('SKIP_ACL', "false"),
    'dataDir': ZOOKEEPER_DATA_DIR,
    'quorumListenOnAllIPs': True,
    'autopurge.snapRetainCount':
        int(os.environ.get('MAX_SNAPSHOT_RETAIN_COUNT', 10)),
    'autopurge.purgeInterval':
        int(os.environ.get('PURGE_INTERVAL', 24)),
    'maxClientCnxns':
        int(os.environ.get('MAX_CLIENT_CONNECTIONS', 60)),
}

# Add the ZooKeeper node list with peer and leader election ports and figure
# out our own ID. ZOOKEEPER_SERVER_IDS contains a comma-separated list of
# node:server_id tuples describing the server ID of each node in the cluster,
# by its container name. If not specified, we assume single-node mode.
if os.environ.get('ZOOKEEPER_SERVER_IDS'):
    servers = os.environ['ZOOKEEPER_SERVER_IDS'].split(',')
    for server in servers:
        node, server_id = server.split(':')
        conf['server.{}'.format(server_id)] = build_node_repr(node)
        if node == CONTAINER_NAME:
            ZOOKEEPER_NODE_ID = server_id

# Verify that the number of declared nodes matches the size of the cluster.
ZOOKEEPER_NODE_COUNT = os.environ.get('ZK_REPLICAS') or \
                        len(get_node_list(DISCOVERY_SERVICE_NAME))
ZOOKEEPER_NODE_COUNT = int(ZOOKEEPER_NODE_COUNT)
ZOOKEEPER_CLUSTER_SIZE = len(
    [i for i in conf.keys() if i.startswith('server.')])

# If no ZOOKEEPER_SERVER_IDS is defined, we expect to be in single-node mode so
# no more than one node can be declared in the cluster.
if ZOOKEEPER_CLUSTER_SIZE == 0 and ZOOKEEPER_NODE_COUNT != 1:
    print(('Missing ZOOKEEPER_SERVER_IDS declaration for ' +
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
          .format(ZOOKEEPER_CLUSTER_SIZE, ZOOKEEPER_NODE_COUNT))
    sys.exit(1)

# Write out the ZooKeeper configuration file.
with open(ZOOKEEPER_CONFIG_FILE, 'w+') as config_file:
    for entry in conf.iteritems():
        config_file.write("%s=%s\n" % entry)

# Setup the logging configuration.
zk_root_logger = ('log4j.rootLogger=' +
                    os.environ.get('LOG_LEVEL', 'INFO'))
log_conf = ''
# By defualt logs go to stdout
if os.environ.get('LOG_TO_STDOUT', 'false').lower() == 'true':
    zk_root_logger += ', stdout'
    log_conf += """# Log4j config, logs to stdout
log4j.appender.stdout=org.apache.log4j.ConsoleAppender
log4j.appender.stdout.layout=org.apache.log4j.PatternLayout
log4j.appender.stdout.layout.ConversionPattern=%s
 """ % (LOG_PATTERN)

if os.environ.get('LOG_TO_FILE', 'true').lower() == 'true':
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
    with open(os.path.join(ZOOKEEPER_DATA_DIR, 'myid'), 'w+') as myid_file:
        myid_file.write('%s\n' % ZOOKEEPER_NODE_ID)
    print('Starting {}, node id#{} of a {}-node ZooKeeper cluster...\n'
          .format(CONTAINER_NAME, ZOOKEEPER_NODE_ID,
                  ZOOKEEPER_CLUSTER_SIZE))
else:
    print('Starting {} as a single-node ZooKeeper cluster...\n'
          .format(CONTAINER_NAME))

jvmflags = [
    '-server',
    '-showversion',
    '-Dvisualvm.display.name="{}/{}"'.format(
        get_environment_name(),
        CONTAINER_NAME),
]

jmx_port = get_specific_port(DISCOVERY_SERVICE_NAME,
                             CONTAINER_NAME, 'jmx', -1)
if jmx_port != -1:
    jvmflags += [
        '-Djava.rmi.server.hostname={}'.format(get_container_host_address()),
        '-Dcom.sun.management.jmxremote.port={}'.format(jmx_port),
        '-Dcom.sun.management.jmxremote.rmi.port={}'.format(jmx_port),
        '-Dcom.sun.management.jmxremote.authenticate=false',
        '-Dcom.sun.management.jmxremote.local.only=false',
        '-Dcom.sun.management.jmxremote.ssl=false',
    ]
os.environ['JVMFLAGS'] = ' '.join(jvmflags) + \
                         ' ' + os.environ.get('JVM_OPTS', '')

# Start ZooKeeper
os.execl('bin/zkServer.sh', 'zookeeper', 'start-foreground')
