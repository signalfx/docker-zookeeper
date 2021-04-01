#!/usr/bin/env bash

# Issue a reconfig command to the first node in the cluster (server.1)
# to remove ourselves from the ensemble

MY_ID=$((${POD_NAME##*-}+1))
ID=${POD_NAME##*-}
MY_FQDN=$POD_NAME.$DISCOVERY_SERVICE_NAME.$NAMESPACE.svc.cluster.local
ZK_SERVER_ONE_FQDN=${MY_FQDN/$ID/0}
if [ "$ZK_SERVER_ONE_FQDN" ]; then
	/opt/zookeeper-3.5.4-beta/bin/zkCli.sh -server $ZK_SERVER_ONE_FQDN:2181 reconfig -remove $MY_ID
fi
