# Dockerfile for ZooKeeper

FROM quay.io/signalfuse/maestro-base:14.04-0.1.8.1
MAINTAINER Maxime Petazzoni <max@signalfuse.com>

# Get latest stable release of ZooKeeper
RUN wget -q -O - http://mirrors.sonic.net/apache/zookeeper/zookeeper-3.4.6/zookeeper-3.4.6.tar.gz \
  | tar -C /opt -xz

ADD run.py /opt/zookeeper-3.4.6/.docker/

WORKDIR /opt/zookeeper-3.4.6/
CMD ["python", "/opt/zookeeper-3.4.6/.docker/run.py"]
