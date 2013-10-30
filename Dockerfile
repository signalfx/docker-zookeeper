# Dockerfile for ZooKeeper

FROM mpetazzoni/sf-base

MAINTAINER Maxime Petazzoni <max@signalfuse.com>

# Get latest stable release of ZooKeeper
RUN wget -q -O - http://apache.mesi.com.ar/zookeeper/zookeeper-3.4.5/zookeeper-3.4.5.tar.gz \
  | tar -C /opt -xz

ADD run.py /opt/zookeeper-3.4.5/.docker/

WORKDIR /opt/zookeeper-3.4.5/
CMD ["python", "/opt/zookeeper-3.4.5/.docker/run.py"]
