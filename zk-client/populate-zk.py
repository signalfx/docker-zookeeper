#!/usr/bin/env python

# Copyright (C) 2015 SignalFx, Inc.  All rights reserved.
#
# Lifecycle check helper for single zookeeper node clusters that helps
# ensure zk data is prepopulated.
#
# Usage: populate_zk.py -h for help

# Author: tedo

import argparse
import logging
import json
import sys

from kazoo.client import KazooClient

def populate_data(zk, realm, data):
    for key, value in data.items():
        key = '/{}{}'.format(realm, key)
        if not zk.exists(key):
            zk.create(key, value.encode('utf-8'), makepath=True)


def main(server, realm, data_file):

    with open(data_file, 'r') as f:
        data = json.load(f)

    zk = KazooClient(hosts=server, timeout=30000)
    started = False
    try:
        zk.start()
        started = True
        populate_data(zk, realm, data)
        return 0
    except Exception as e:
        logging.error('Error: %s' % e)
        return 1
    finally:
        if started:
            zk.stop()

if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('-c', '--connect',
                        help=('Comma-separated list of zk hosts to connect to '
                              '(e.g. 127.0.0.1:2181,zk-0.domain:2181'))
    parser.add_argument('-r', '--realm', help='The realm being bootstrapped')
    parser.add_argument('file',
                        help=('Data file to load. The data is expected to be '
                              'a JSON object with the key, value pairs to '
                              'populate in ZooKeeper under the realm node.'))
    options = parser.parse_args()
    logging.basicConfig(stream=sys.stderr, level=logging.ERROR)
    sys.exit(main(options.connect, options.realm, options.file))
