#!/usr/bin/env bash

# Issue a reconfig command to the first node in the cluster (server.1)
# to remove ourselves from the ensemble

ID=$((${POD_NAME##*-}+1))
ZK_SERVER_ONE_FQDN=$(echo config | nc localhost 2181 | grep server.1 | cut -d"=" -f2 | cut -d":" -f1)
if [ -z "$ZK_SERVER_ONE_FQDN" ]; then
  exit 0
else
	/opt/zookeeper-3.5.4-beta/bin/zkCli.sh -server $ZK_SERVER_ONE_FQDN:2181 reconfig -remove $ID
fi
