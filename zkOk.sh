#!/usr/bin/env bash
# zkOk.sh uses the ruok ZooKeeper four letter word to determine if the instance
# is healthy. Returns with exit code 0 if server responds that it is
# healthy, or 1 if the server fails to respond. This script will be used by
# kubelet to perform health checks.

ZK_CLIENT_PORT=${ZK_CLIENT_PORT:-2181}
OK=$(echo ruok | nc 127.0.0.1 $ZK_CLIENT_PORT)
if [ "$OK" == "imok" ]; then
	exit 0
else
	exit 1
fi
