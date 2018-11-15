# Dockerfile for ZooKeeper

FROM quay.io/signalfuse/signalfx-base:alp-3.8-jdk8

LABEL \
  maintainer="Jina Jain <jina@signalfx.com>" \

# Get latest stable release of ZooKeeper
RUN wget -q -O - http://apache.claz.org/zookeeper/zookeeper-3.4.13/zookeeper-3.4.13.tar.gz \
  | tar -C /opt -xz

ADD run.py /opt/zookeeper-3.4.13/.docker/
ADD zkOk.sh /opt/zookeeper-3.4.13/
WORKDIR /opt/zookeeper-3.4.13/
CMD ["python", "/opt/zookeeper-3.4.13/.docker/run.py"]
