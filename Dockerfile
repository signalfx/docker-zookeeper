# Dockerfile for ZooKeeper

FROM quay.io/signalfuse/maestro-base:alp-3.2-jdk8
MAINTAINER Maxime Petazzoni <max@signalfx.com>

# Get latest stable release of ZooKeeper
RUN wget -q -O - http://apache.claz.org/zookeeper/zookeeper-3.4.12/zookeeper-3.4.12.tar.gz \
  | tar -C /opt -xz

ADD run.py /opt/zookeeper-3.4.12/.docker/

WORKDIR /opt/zookeeper-3.4.12/
CMD ["python", "/opt/zookeeper-3.4.12/.docker/run.py"]
