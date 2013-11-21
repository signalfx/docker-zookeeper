# Dockerfile for ZooKeeper

FROM mpetazzoni/maestro-base

MAINTAINER Maxime Petazzoni <max@signalfuse.com>

# Install Maestro for guest utils
RUN apt-get update
RUN apt-get -y install python python-setuptools
RUN easy_install http://github.com/signalfuse/maestro-ng/archive/maestro-0.1.0.zip

# Get latest stable release of ZooKeeper
RUN wget -q -O - http://apache.mesi.com.ar/zookeeper/zookeeper-3.4.5/zookeeper-3.4.5.tar.gz \
  | tar -C /opt -xz

ADD run.py /opt/zookeeper-3.4.5/.docker/

WORKDIR /opt/zookeeper-3.4.5/
VOLUME /var/lib/zookeeper
CMD ["python", "/opt/zookeeper-3.4.5/.docker/run.py"]
