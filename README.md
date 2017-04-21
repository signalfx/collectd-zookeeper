# CollectD ZooKeeper plugin

CollectD plugin for getting metrics and information from
[ZooKeeper](http://zookeeper.apache.org) servers. Based off the
ZooKeeper monitoring script
[check_zookeeper.py](https://svn.apache.org/repos/asf/zookeeper/trunk/src/contrib/monitoring/check_zookeeper.py).

Requires ZooKeeper 3.4.0 or greater in order to use the `mntr` [four
letter word
command](http://zookeeper.apache.org/doc/trunk/zookeeperAdmin.html#sc_zkCommands).

TODO: if support for earlier versions is needed, add `srvr` command,
available in since 3.3.0, or `stat` (fetches extra uneeded data but
available pre-3.3).

# Install

1. Checkout this repository somewhere on your system accessible by
   collectd; for example as
   `/usr/share/collectd/collectd-zookeeper`
1. Configure the plugin (see below).
1. Restart collectd.

## Configuration

Add the following to your collectd config:

```
<LoadPlugin "python">
  Globals true
</LoadPlugin>

<Plugin python>
  ModulePath "/usr/share/collectd/collectd-zookeeper"
  Import "zk-collectd"

  <Module "zk-collectd">
    Hosts "localhost"
    Port 2181
  </Module>

  # You may have as many Module sections as you want
  <Module "zk-collectd">
    Hosts "localhost"
    Port 2182
    Instance "dev"
  </Module>
</Plugin>
```

# Metrics

All metrics are reported with the `plugin:zookeeper` dimension. Additionally,
if you specify an `Instance` in your `Module` configuration block, its value
will be reported as the `plugin_instance` dimension.

zk_is_leader is a synthetic metric which is 0 if the contents of zk_server_state is 'follower'.
zk_service_health is a synthetic metric which tracks if service is running and servicing requests.

# License

Available under the terms of the Apache Software License v2. See LICENSE
file for details.
