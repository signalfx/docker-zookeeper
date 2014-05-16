# Dockerfile for ZooKeeper

FROM quay.io/signalfuse/maestro-base:0.1.7.1
MAINTAINER Maxime Petazzoni <max@signalfuse.com>

# Get latest stable release of ZooKeeper
RUN wget -q -O - http://mirrors.sonic.net/apache/zookeeper/zookeeper-3.4.5/zookeeper-3.4.5.tar.gz \
  | tar -C /opt -xz

ADD jmxagent.jar /opt/zookeeper-3.4.5/lib/
ADD run.py /opt/zookeeper-3.4.5/.docker/

WORKDIR /opt/zookeeper-3.4.5/
VOLUME /var/lib/zookeeper
VOLUME /var/log/zookeeper
CMD ["python", "/opt/zookeeper-3.4.5/.docker/run.py"]
