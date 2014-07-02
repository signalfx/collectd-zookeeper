#!/bin/bash
cd /opt
sudo git clone git@github.com:signalfuse/collectd-zookeeper.git
if [ $? -ne 0 ]; then
  echo "Unable to clone zookeeper plugin."
  exit 1
fi

echo 'Include "/opt/collectd-zookeeper/zk-collectd.conf"' | sudo tee -a /etc/collectd/collectd.conf

sudo mkdir -p /usr/share/collectd/python
if [ $? -ne 0 ]; then
  echo "Unable to make plugin directory."
  exit 1
fi

sudo ln -s /opt/collectd-zookeeper/zk-collectd.py /usr/share/collectd/python/zk-collectd.py
if [ $? -ne 0 ]; then
  echo "Unable to copy over zookeeper plugin."
  exit 1
fi