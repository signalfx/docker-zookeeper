#!/usr/bin/env python

# Start script for the ZooKeeper service.
#
# This is where service configuration before starting ZooKeeper can be
# performed, if needed, for example to configure the ZooKeeper cluster peers in
# the configuration file.

import os
import sys

os.chdir(os.path.join(
    os.path.dirname(os.path.abspath(__file__)),
    '..'))

ZOOKEEPER_CONFIG_FILE = 'conf/zoo.cfg'

# This gets filled in automatically from ZOOKEEPER_NODE_LIST, if needed.
ZOOKEEPER_NODES = []

# Environment variables driving the ZooKeeper configuration and their defaults.
ZOOKEEPER_CONFIG_NODE_ID = int(os.environ.get('ZOOKEEPER_CONFIG_NODE_ID', 0))
ZOOKEEPER_CONFIG_DATA_DIR = os.environ.get('ZOOKEEPER_CONFIG_DATA_DIR', '/var/lib/zookeeper')
ZOOKEEPER_CONFIG_CLIENT_PORT = int(os.environ.get('ZOOKEEPER_CONFIG_CLIENT_PORT', 2181))
ZOOKEEPER_CONFIG_PEER_PORT = int(os.environ.get('ZOOKEEPER_CONFIG_PEER_PORT', 2888))
ZOOKEEPER_CONFIG_LEADER_ELECTION_PORT = int(os.environ.get('ZOOKEEPER_CONFIG_LEADER_ELECTION_PORT', 3888))
# TODO: support heap settings (conf/java.env and JVMARGS)

# Parse and validate the ZooKeeper node list if we're part of a multi-node
# cluster deployment.
if ZOOKEEPER_CONFIG_NODE_ID:
    ZOOKEEPER_NODE_LIST = os.environ.get('ZOOKEEPER_NODE_LIST', None)
    if not ZOOKEEPER_NODE_LIST:
        sys.stderr.write('A ZooKeeper instance part of a multi-node cluster cannot '
            'be deployed without a ZooKeeper node list (set ZOOKEEPER_NODE_LIST).\n')
        sys.exit(1)

    for node_id, details in enumerate(ZOOKEEPER_NODE_LIST.split(','), 1):
        node = details.split(':')
        if len(node) < 4:
            sys.stderr.write('Invalid ZooKeeper node definition: %s !\n' % details)
            sys.exit(1)
        ZOOKEEPER_NODES.append({
            'id': node_id,
            'host': node[0],
            'client_port': int(node[1]),
            'peer_port': int(node[2]),
            'leader_election_port': int(node[3])
        })

    # We must be present in the ZOOKEEPER_NODE_LIST
    if len(ZOOKEEPER_NODES) < ZOOKEEPER_CONFIG_NODE_ID:
        sys.stderr.write('Incomplete ZooKeeper node list!\n')
        sys.exit(1)

    # Valide port numbers in the list match our own configuration
    node = ZOOKEEPER_NODES[ZOOKEEPER_CONFIG_NODE_ID-1]
    if ZOOKEEPER_CONFIG_CLIENT_PORT != node['client_port'] or \
            ZOOKEEPER_CONFIG_PEER_PORT != node['peer_port'] or \
            ZOOKEEPER_CONFIG_LEADER_ELECTION_PORT != node['leader_election_port']:
        sys.stderr.write('Mismatched ports with node list for node %d!\n' %
            ZOOKEEPER_CONFIG_NODE_ID)
        sys.exit(1)

with open(ZOOKEEPER_CONFIG_FILE, 'w+') as conf:
    conf.write('\n'.join([
        'tickTime=2000',
        'initLimit=10',
        'syncLimit=5',
        'dataDir=%s' % ZOOKEEPER_CONFIG_DATA_DIR,
        'clientPort=%d' % ZOOKEEPER_CONFIG_CLIENT_PORT]))
    conf.write('\n')

    for node in ZOOKEEPER_NODES:
        conf.write('server.%(id)d=%(host)s:%(peer_port)d:%(leader_election_port)d\n' % node)

# When a node ID is specified, we're running in multi-node cluster mode and we
# also need to generate the 'myid' file.
if ZOOKEEPER_CONFIG_NODE_ID:
    if not os.path.exists(ZOOKEEPER_CONFIG_DATA_DIR):
        os.makedirs(ZOOKEEPER_CONFIG_DATA_DIR, mode=0750)
    with open(os.path.join(ZOOKEEPER_CONFIG_DATA_DIR, 'myid'), 'w+') as myid:
        myid.write('%s\n' % ZOOKEEPER_CONFIG_NODE_ID)
    print 'Configured node #%d of a %d-node ZooKeeper cluster.' % \
            (ZOOKEEPER_CONFIG_NODE_ID, len(ZOOKEEPER_NODES))
else:
    print 'Configured single-node ZooKeeper instance.'

# Start ZooKeeper
os.execl('bin/zkServer.sh', 'zookeeper', 'start-foreground')
