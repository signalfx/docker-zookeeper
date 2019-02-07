#!/usr/bin/env bash

# Issue a reconfig command to the first node in the cluster (server.1)
# to register ourselves with the ensemble

MY_ID=server.$((${POD_NAME##*-}+1))
MY_FQDN=$POD_NAME.$DISCOVERY_SERVICE_NAME.$NAMESPACE.svc.cluster.local
ZK_SERVER_ONE_FQDN=$(echo config | nc localhost 2181 | grep server.1 | cut -d"=" -f2 | cut -d":" -f1)
if [ -z "$ZK_SERVER_ONE_FQDN" ]; then
  echo "reconfig -add $MY_ID=$MY_FQDN:2888:3888:participant;0.0.0.0:2181" | nc $ZK_SERVER_ONE_FQDN 2181
else
	exit 0
fi
