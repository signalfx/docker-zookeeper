#!/bin/bash -e

if [ "$RUN_AS_MAESTRO" != "true" ]; then
    exec "$@"
else
    # Setup writes to config
    if [ -d conf ]; then
      chown -R maestro:maestro conf
    fi

    # Data directories
    IFS=,
    for x in ${PATH_DATA:-/var/lib/zookeeper}; do
        if [ -d $x ]; then
            chown -R maestro:maestro  ${x}
        fi
    done
    unset IFS

    # Log directory
    if [ -d /var/log/zookeeper ]; then
        chown -R maestro:maestro /var/log/zookeeper/
    fi

    exec su-exec maestro:maestro "$@"
fi
