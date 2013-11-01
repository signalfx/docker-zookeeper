#!/usr/bin/env python

# Start script for the ZooKeeper service.
#
# This is where service configuration before starting ZooKeeper can be
# performed, if needed, for example to configure the ZooKeeper cluster peers in
# the configuration file.

import os
import re
import sys

os.chdir(os.path.join(
    os.path.dirname(os.path.abspath(__file__)),
    '..'))

ZOOKEEPER_CONFIG_FILE = 'conf/zoo.cfg'
ZOOKEEPER_CONFIG_DATA_DIR = '/var/lib/zookeeper'

CONTAINER_NAME = os.environ.get('CONTAINER_NAME', '')
assert CONTAINER_NAME, 'Container name is missing!'
ZOOKEEPER_CONFIG_BASE = re.sub(r'[^\w]', '_', CONTAINER_NAME).upper()

ZOOKEEPER_CONFIG_CLIENT_PORT = int(os.environ.get('ZOOKEEPER_%s_CLIENT_PORT' % ZOOKEEPER_CONFIG_BASE, 2181))
ZOOKEEPER_CONFIG_PEER_PORT = int(os.environ.get('ZOOKEEPER_%s_PEER_PORT' % ZOOKEEPER_CONFIG_BASE, 2888))
ZOOKEEPER_CONFIG_LEADER_ELECTION_PORT = int(os.environ.get('ZOOKEEPER_%s_LEADER_ELECTION_PORT' % ZOOKEEPER_CONFIG_BASE, 3888))

def write_myid(node_id):
    """Helper function to create the 'myid' file containing the node ID passed
    as argument."""
    if not os.path.exists(ZOOKEEPER_CONFIG_DATA_DIR):
        os.makedirs(ZOOKEEPER_CONFIG_DATA_DIR, mode=0750)
    with open(os.path.join(ZOOKEEPER_CONFIG_DATA_DIR, 'myid'), 'w+') as myid:
        myid.write('%s\n' % node_id)

ZOOKEEPER_NODES = []
for k in sorted(os.environ.keys()):
    m = re.match(r'^ZOOKEEPER_(\w+)_HOST$', k)
    if m: ZOOKEEPER_NODES.append(m.group(1))

with open(ZOOKEEPER_CONFIG_FILE, 'w+') as conf:
    conf.write("""# ZooKeeper configuration for %(node_name)s
tickTime=2000
initLimit=10
syncLimit=5
dataDir=%(data_dir)s
clientPort=%(client_port)d
""" % {
    'node_name': CONTAINER_NAME,
    'data_dir': ZOOKEEPER_CONFIG_DATA_DIR,
    'client_port': ZOOKEEPER_CONFIG_CLIENT_PORT,
    })

    # Add the ZooKeeper node list with peer and leader election ports.
    for id, name in enumerate(ZOOKEEPER_NODES, 1):
        conf.write('server.%d=%s:%d:%d\n' % (id,
            os.environ['ZOOKEEPER_%s_HOST' % name],
            int(os.environ['ZOOKEEPER_%s_PEER_PORT' % name]),
            int(os.environ['ZOOKEEPER_%s_LEADER_ELECTION_PORT' % name])))
        # Write out the 'myid' file in the data directory if we ourselves in
        # the node list.
        if ZOOKEEPER_CONFIG_BASE == name:
            write_myid(id)

# Start ZooKeeper
os.execl('bin/zkServer.sh', 'zookeeper', 'start-foreground')
