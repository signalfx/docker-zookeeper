# Dockerfile for ZooKeeper

FROM quay.io/signalfuse/signalfx-base:alp-3.13-jdk8
MAINTAINER Maxime Petazzoni <max@signalfx.com>

# Get latest stable release of ZooKeeper
RUN wget -q -O - https://archive.apache.org/dist/zookeeper/zookeeper-3.5.9/apache-zookeeper-3.5.9-bin.tar.gz \
  | tar -C /opt -xz

ADD run.py /opt/apache-zookeeper-3.5.9-bin/.docker/
ADD entrypoint.sh /opt/apache-zookeeper-3.5.9-bin/.docker/
ADD zkOk.sh /opt/apache-zookeeper-3.5.9-bin/
ADD preStop.sh /opt/apache-zookeeper-3.5.9-bin/
ADD postStart.sh /opt/apache-zookeeper-3.5.9-bin/

# That's unused, since we don't enable admin server. Removing to prevent
# CVE-2020-27223 from showing up in security scans.
RUN rm /opt/apache-zookeeper-3.5.9-bin/lib/jetty-http*

# Upgrade netty-buffer to remediate CVE-2021-21290.
RUN rm /opt/apache-zookeeper-3.5.9-bin/lib/netty-buffer-4.1.50.Final.jar
RUN wget -q -O /opt/apache-zookeeper-3.5.9-bin/lib/netty-buffer-4.1.60.Final.jar https://repo1.maven.org/maven2/io/netty/netty-buffer/4.1.60.Final/netty-buffer-4.1.60.Final.jar

WORKDIR /opt/apache-zookeeper-3.5.9-bin/

# Keep RUN_CMD in sync with ENTRYPOINT and CMD or just use the wrapped shell with ENV VAR
ENV RUN_CMD=".docker/entrypoint.sh python /opt/apache-zookeeper-3.5.9-bin/.docker/run.py"
# CMD ["sh", "-c", "$RUN_CMD"]
ENTRYPOINT [".docker/entrypoint.sh"]
CMD ["python", "/opt/apache-zookeeper-3.5.9-bin/.docker/run.py"]
