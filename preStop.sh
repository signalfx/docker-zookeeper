#!/usr/bin/env bash

# Issue a reconfig command to the first node in the cluster (server.1)
# to remove ourselves from the ensemble

ID=$(cat /var/lib/zookeeper/myid)
ZK_SERVER_ONE_FQDN=$(echo config | nc localhost 2181 | grep server.1 | cut -d"=" -f2 | cut -d":" -f1)
echo "reconfig -remove $ID" | nc $ZK_SERVER_ONE_FQDN 2181
