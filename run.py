#!/usr/bin/env python

# Copyright (C) 2013 SignalFuse, Inc.

# Start script for the ZooKeeper service.

import os
import re
import sys

if __name__ != '__main__':
    sys.stderr.write('This script is only meant to be executed.\n')
    sys.exit(1)

os.chdir(os.path.join(
    os.path.dirname(os.path.abspath(__file__)),
    '..'))

ZOOKEEPER_CONFIG_FILE = 'conf/zoo.cfg'

# Get container/instance name.
CONTAINER_NAME = os.environ.get('CONTAINER_NAME', '')
assert CONTAINER_NAME, 'Container name is missing!'
CONFIG_BASE = re.sub(r'[^\w]', '_', CONTAINER_NAME).upper()

ZOOKEEPER_DATA_DIR = '/var/lib/zookeeper'
ZOOKEEPER_NODE_ID = None

# Gather configuration settings from environment.
ZOOKEEPER_CLIENT_PORT = int(os.environ.get('ZOOKEEPER_{}_CLIENT_PORT'.format(CONFIG_BASE), 2181))
ZOOKEEPER_PEER_PORT = int(os.environ.get('ZOOKEEPER_{}_PEER_PORT'.format(CONFIG_BASE), 2888))
ZOOKEEPER_LEADER_ELECTION_PORT = int(os.environ.get('ZOOKEEPER_{}_LEADER_ELECTION_PORT'.format(CONFIG_BASE), 3888))

# Write out the ZooKeeper configuration file.
with open(ZOOKEEPER_CONFIG_FILE, 'w+') as conf:
    conf.write("""# ZooKeeper configuration for %(node_name)s
tickTime=2000
initLimit=10
syncLimit=5
dataDir=%(data_dir)s
clientPort=%(client_port)d
""" % {
    'node_name': CONTAINER_NAME,
    'data_dir': ZOOKEEPER_DATA_DIR,
    'client_port': ZOOKEEPER_CLIENT_PORT,
    })

    def extract_zk_node_name(s):
        m = re.match(r'^ZOOKEEPER_(\w+)_HOST$', s)
        return m and m.group(1) or None

    # Add the ZooKeeper node list with peer and leader election ports.
    # First, gather ZooKeeper nodes from the environment.
    for id, name in enumerate(filter(None,
        map(extract_zk_node_name, sorted(os.environ.keys()))), 1):
        conf.write('server.%d=%s:%d:%d\n' % (id,
            os.environ['ZOOKEEPER_%s_HOST' % name],
            int(os.environ['ZOOKEEPER_%s_PEER_PORT' % name]),
            int(os.environ['ZOOKEEPER_%s_LEADER_ELECTION_PORT' % name])))
        if CONFIG_BASE == name:
            ZOOKEEPER_NODE_ID = id

# Write out the 'myid' file in the data directory if we found ourselves in the
# node list.
if ZOOKEEPER_NODE_ID:
    if not os.path.exists(ZOOKEEPER_DATA_DIR):
        os.makedirs(ZOOKEEPER_DATA_DIR, mode=0750)
    with open(os.path.join(ZOOKEEPER_DATA_DIR, 'myid'), 'w+') as f:
        f.write('%s\n' % ZOOKEEPER_NODE_ID)

# Start ZooKeeper
os.execl('bin/zkServer.sh', 'zookeeper', 'start-foreground')
