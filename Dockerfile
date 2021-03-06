# Dockerfile for ZooKeeper

FROM quay.io/signalfuse/maestro-base:alp-3.8-jdk8
MAINTAINER Maxime Petazzoni <max@signalfx.com>

# Get latest stable release of ZooKeeper
RUN wget -q -O - https://www.apache.org/dist/zookeeper/zookeeper-3.5.5/apache-zookeeper-3.5.5.tar.gz \
  | tar -C /opt -xz

ADD run.py /opt/apache-zookeeper-3.5.5/.docker/
ADD entrypoint.sh /opt/apache-zookeeper-3.5.5/.docker/

WORKDIR /opt/apache-zookeeper-3.5.5/

# Keep RUN_CMD in sync with ENTRYPOINT and CMD or just use the wrapped shell with ENV VAR
ENV RUN_CMD=".docker/entrypoint.sh python /opt/apache-zookeeper-3.5.5/.docker/run.py"
# CMD ["sh", "-c", "$RUN_CMD"]
ENTRYPOINT [".docker/entrypoint.sh"]
CMD ["python", "/opt/apache-zookeeper-3.5.5/.docker/run.py"]
