#!/usr/bin/env python

# Copyright (C) 2015 SignalFx, Inc. All rights reserved.
#
# Lifecycle check for ZooKeeper. Opens a connection to the client port, sends
# 'ruok' and expects 'imok' back.

import argparse
import socket
import sys

def recv(s, maxlen=2048):
    message = b''
    while len(message) < maxlen:
        chunk = s.recv(64)
        if not chunk:
            break
        message += chunk
    return message


def main(host, port):
    s = socket.socket()
    try:
        s.settimeout(0.5)
        s.connect((host, port))
        s.sendall(b'ruok')
        return recv(s) == b'imok'
    except:
        return False
    finally:
        s.close()

if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('-s', '--host', default='127.0.0.1', type=str,
                        help=('zookeeper server\'s hostname/ipaddr'))
    parser.add_argument('-p', '--port', default=2181, type=int,
                        help=('Port number to connect to'))
    args = parser.parse_args()
    sys.exit(0 if main(args.host, args.port) else 1)
