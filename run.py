#!/usr/bin/env python
"""
Startup script for the ZooKeeper service.
"""

from __future__ import print_function
import pprint
import os
import re

import kubefxutils

os.chdir(os.path.join(
    os.path.dirname(os.path.abspath(__file__)),
    '..'))

K8S_HELPER = kubefxutils.K8sHelper()
ZK_CONFIG_FILE = os.path.join('conf', 'zoo.cfg')
ZK_LOG_CONFIG_FILE = os.path.join('conf', 'log4j.properties')
ZK_DATA_DIR = os.environ.get('ZK_DATA_DIR', '/var/lib/zookeeper')

try:
    ZK_NAME, ZK_SERVER_ID = re.match(r'(.*)-([0-9]+)$',
                                     K8S_HELPER.pod_name).groups()
except AttributeError:
    raise ('Failed to extract the ordinal index from hostname {}. Please '
           'deploy zookeeper as a StatefulSet'.format(K8S_HELPER.pod_name))
ZK_SERVER_ID = str(int(ZK_SERVER_ID) + 1)

ZK_FQDN = K8S_HELPER.get_pod_dns_name()
if ZK_FQDN is None:
    raise ('Failed to get zk pod\'s FQDN.'
           ' Please deploy zookeeper as a StatefulSet.')
ZK_DOMAIN = ZK_FQDN.split('.', 1)[1]

ZK_REPLICAS = os.environ.get('ZK_REPLICAS')
if ZK_REPLICAS is None:
    raise ('Please provide the number of zk servers in this ensemble as '
           'ZK_REPLICAS environment variable.')

ZK_HS_SVC = ZK_DOMAIN.split('.', 1)[0]
PORTS = {}
for port in ['client', 'peer', 'election']:
    port_num = os.environ.get('ZK_{}_PORT'.format(port.upper())) or \
        K8S_HELPER.get_port('client', service=ZK_HS_SVC)
    if port_num is None:
        raise 'Could not find port number for the port name {}'.format(port)
    PORTS[port] = port_num

LOG_DIR = os.environ.get('LOG_DIR',
                         '/var/log/{}'.format(K8S_HELPER.service_name))
LOG_PATTERN = (
    "%d{yyyy'-'MM'-'dd'T'HH:mm:ss.SSSXXX} %-5p [%-35.35t] [%-36.36c]: %m%n")


def write_zk_config():
    """Build and write the ZooKeeper node configuration."""
    conf = {
        'tickTime': int(os.environ.get('ZK_TICK_TIME', 2000)),
        'initLimit': int(os.environ.get('ZK_INIT_TIME', 10)),
        'syncLimit': int(os.environ.get('ZK_SYNC_LIMIT', 5)),
        'dataDir': ZK_DATA_DIR,
        'clientPort': PORTS['client'],
        'quorumListenOnAllIPs': True,
        'autopurge.snapRetainCount':
            int(os.environ.get('MAX_SNAPSHOT_RETAIN_COUNT', 10)),
        'autopurge.purgeInterval':
            int(os.environ.get('PURGE_INTERVAL', 24)),
        'maxClientCnxns':
            int(os.environ.get('MAX_CLIENT_CONNECTIONS', 60)),
    }
    # Add the ZooKeeper node list with peer and leader election ports.

    peer_port = PORTS['peer']
    election_port = PORTS['election']
    for replica in range(1, int(ZK_REPLICAS)+1):
        conf['server.{}'.format(replica)] = '{}-{}.{}:{}:{}'.format(
            ZK_NAME, replica - 1, ZK_DOMAIN, peer_port, election_port)
    # Write out the ZooKeeper configuration file.
    print('Writing ZK config file with following config.')
    with open(ZK_CONFIG_FILE, 'w+') as config_file:
        for entry in conf.iteritems():
            config_file.write("%s=%s\n" % entry)
            print("%s=%s\n" % entry)

def write_log_prop():
    """Setup the logging configuration."""
    zk_root_logger = ('log4j.rootLogger=' +
                      os.environ.get('LOG_LEVEL', 'INFO'))
    log_conf = ''
    # By defualt logs go to stdout
    if os.environ.get('LOG_TO_STDOUT', 'true').lower() == 'true':
        zk_root_logger += ', stdout'
        log_conf += """# Log4j config, logs to stdout
log4j.appender.stdout=org.apache.log4j.ConsoleAppender
log4j.appender.stdout.layout=org.apache.log4j.PatternLayout
log4j.appender.stdout.layout.ConversionPattern=%s
    """ % (LOG_PATTERN)

    if os.environ.get('LOG_TO_FILE', 'false').lower() == 'true':
        zk_root_logger += ', R'
        log_conf += """# Log4j configuration, logs to rotating file
log4j.appender.R=org.apache.log4j.RollingFileAppender
log4j.appender.R.File=%s
log4j.appender.R.MaxFileSize=100MB
log4j.appender.R.MaxBackupIndex=10
log4j.appender.R.layout=org.apache.log4j.PatternLayout
log4j.appender.R.layout.ConversionPattern=%s
    """ % (os.path.join(LOG_DIR, K8S_HELPER.pod_name + '.log'), LOG_PATTERN)

    log_conf = zk_root_logger + '\n' + log_conf
    with open(ZK_LOG_CONFIG_FILE, 'w+') as log_file:
        log_file.write(log_conf)
        print('ZK logging configuration - \n %s' % log_conf)

def write_my_id():
    """Write out the 'myid' file in the data directory if in cluster mode."""
    if ZK_REPLICAS > 1:
        if not os.path.exists(ZK_DATA_DIR):
            os.makedirs(ZK_DATA_DIR, mode=0750)
        with open(os.path.join(ZK_DATA_DIR, 'myid'), 'w+') as myid_file:
            myid_file.write('%s\n' % ZK_SERVER_ID)
        print('Starting {}, node id#{} of a {}-node ZooKeeper cluster...\n'
              .format(K8S_HELPER.pod_name, ZK_SERVER_ID,
                      ZK_REPLICAS))
    else:
        print('Starting {} as a single-node ZooKeeper cluster...\n'
              .format(K8S_HELPER.pod_name))

def create_java_env():
    """ Create JVM configuration"""
    jvmflags = [
        '-server',
        '-showversion',
        '-Dvisualvm.display.name="{}/{}"'.format(
            K8S_HELPER.get_sfx_realm() or K8S_HELPER.namespace,
            K8S_HELPER.pod_name),
    ]
    jmx_port = os.environ.get('ZK_JMX_PORT') or \
        K8S_HELPER.get_port('jmx', service=ZK_HS_SVC)
    if jmx_port is not None:
        jvmflags += [
            '-Djava.rmi.server.hostname={}'.format(ZK_FQDN),
            '-Dcom.sun.management.jmxremote.port={}'.format(jmx_port),
            '-Dcom.sun.management.jmxremote.rmi.port={}'.format(jmx_port),
            '-Dcom.sun.management.jmxremote.authenticate=false',
            '-Dcom.sun.management.jmxremote.local.only=false',
            '-Dcom.sun.management.jmxremote.ssl=false',
        ]
    os.environ['JVMFLAGS'] = ' '.join(jvmflags) + \
                             ' ' + os.environ.get('JVM_OPTS', '')

write_zk_config()
write_log_prop()
write_my_id()
create_java_env()

# Start ZooKeeper
os.execl('bin/zkServer.sh', 'zookeeper', 'start-foreground')
