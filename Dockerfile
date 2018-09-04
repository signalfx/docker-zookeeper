# Dockerfile for ZooKeeper

FROM quay.io/signalfuse/maestro-base:alp-3.4-jdk8
MAINTAINER Maxime Petazzoni <max@signalfx.com>

# Get latest stable release of ZooKeeper
RUN wget -q -O - http://apache.claz.org/zookeeper/zookeeper-3.4.13/zookeeper-3.4.13.tar.gz \
  | tar -C /opt -xz

ADD run.py /opt/zookeeper-3.4.13/.docker/

WORKDIR /opt/zookeeper-3.4.13/
CMD ["python", "/opt/zookeeper-3.4.13/.docker/run.py"]
