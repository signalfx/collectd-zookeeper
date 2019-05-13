#!/usr/bin/env python

#  Licensed to the Apache Software Foundation (ASF) under one or more
#  contributor license agreements.  See the NOTICE file distributed with this
#  work for additional information regarding copyright ownership.  The ASF
#  licenses this file to you under the Apache License, Version 2.0 (the
#  "License"); you may not use this file except in compliance with the License.
#  You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS, WITHOUT
# WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the
# License for the specific language governing permissions and limitations under
# the License.

"""Check Zookeeper Cluster.

Requires ZooKeeper 3.4.0 or greater. The script needs the 'mntr' 4-letter word
command (patch ZOOKEEPER-744) that was now commited to the trunk. The script
also works with ZooKeeper 3.3.x but in a limited way.
"""

import collectd
import socket

CONFIGS = []

ZK_HOSTS = ["localhost"]
ZK_PORT = 2181
ZK_INSTANCE = ""
COUNTERS = set(["zk_packets_received", "zk_packets_sent", "zk_fsync_threshold_exceed_count"])
# 4-letter cmds and any expected response
RUOK_CMD = "ruok"
IMOK_RESP = "imok"
MNTR_CMD = "mntr"


class ZooKeeperServer(object):

    def __init__(self, host='localhost', port='2181', timeout=1):
        self._address = (host, int(port))
        self._timeout = timeout

    def get_stats(self):
        """Get ZooKeeper server stats as a map."""
        stats = {}
        # methods for each four-letter cmd
        stats.update(self._get_health_stat())
        stats.update(self._get_mntr_stats())
        return stats

    def _create_socket(self):
        return socket.socket()

    def _send_cmd(self, cmd):
        """Send a 4letter word command to the server."""
        response = ""
        s = self._create_socket()

        try:
            s.settimeout(self._timeout)

            s.connect(self._address)
            s.send(cmd)

            response = s.recv(2048)
            s.close()
        except socket.timeout:
            log('Service not healthy: timed out calling "%s"' % cmd)
        except socket.error, e:
            log('Service not healthy: error calling "%s": %s' % (cmd, e))

        return response

    def _get_health_stat(self):
        """Send the 'ruok' 4letter word command and parse the output."""
        response = self._send_cmd(RUOK_CMD)
        return {'zk_service_health': int(response == IMOK_RESP)}

    def _get_mntr_stats(self):
        """Send 'mntr' 4letter word command and parse the output."""
        response = self._send_cmd(MNTR_CMD)
        result = {}

        # If instance stops serving requests (e.g. loses quorum) it still
        # returns "imok" to ruok query but will force close any client
        # connections and return an error string to all other 4 letter commands.
        # In this situation we should override zk_service_health metric
        # initially set in _get_health_stat as it's definitely not in a healthy
        # state.
        if response == 'This ZooKeeper instance is not currently serving requests\n':
            return {
                'zk_service_health': 0,
                'zk_version': 'UNKNOWN',
            }

        for line in response.splitlines():
            try:
                key, value = self._parse_line(line)
                if key == 'zk_server_state':
                    result['zk_is_leader'] = int(value != 'follower')
                else:
                    result[key] = value
            except ValueError:
                # Ignore broken lines.
                pass

        return result

    def _parse_line(self, line):
        try:
            key, value = map(str.strip, line.split('\t'))
        except ValueError:
            raise ValueError('Found invalid line: %s' % line)

        if not key:
            raise ValueError('The key is mandatory and should not be empty')

        try:
            value = int(value)
        except (TypeError, ValueError):
            pass

        return key, value


def read_callback():
    """Get stats for all the servers in the cluster."""
    stats = {}
    for conf in CONFIGS:
        for host in conf['hosts']:
            zk = ZooKeeperServer(host, conf['port'])
            stats = zk.get_stats()
            zk_version = stats['zk_version'].split(',')[0]
            del stats['zk_version']
            for k, v in stats.items():
                try:
                    val = collectd.Values(plugin='zookeeper',
                                          meta={'0': True})
                    val.type = 'counter' if k in COUNTERS else 'gauge'
                    val.type_instance = k
                    val.values = [v]
                    val.plugin_instance = "%s[zk_version=%s]" % (
                        conf['instance'], zk_version
                    )
                    val.dispatch()
                except (TypeError, ValueError):
                    log(('error dispatching stat; host=%s, '
                         'key=%s, val=%s') % (host, k, v))
                    pass

    return stats


def configure_callback(conf):
    """Received configuration information"""
    zk_hosts = ZK_HOSTS
    zk_port = ZK_PORT
    zk_instance = ZK_INSTANCE
    for node in conf.children:
        if node.key == 'Hosts':
            if len(node.values[0]) > 0:
                zk_hosts = [host.strip() for host in node.values[0].split(',')]
            else:
                log(('ERROR: Invalid Hosts string. '
                     'Using default of %s') % zk_hosts)
        elif node.key == 'Port':
            if isinstance(node.values[0], (float, int)) and node.values[0] > 0:
                zk_port = node.values[0]
            else:
                log(('ERROR: Invalid Port number. '
                     'Using default of %s') % zk_port)
        elif node.key == 'Instance':
            if len(node.values[0]) > 0:
                zk_instance = node.values[0]
            else:
                log(('ERROR: Invalid Instance string. '
                     'Using default of %s') % zk_instance)
        else:
            collectd.warning('zookeeper plugin: Unknown config key: %s.'
                             % node.key)
            continue

    config = {'hosts': zk_hosts,
              'port': zk_port,
              'instance': zk_instance}
    log('Configured with %s.' % config)
    CONFIGS.append(config)


def log(msg):
    collectd.info('zookeeper plugin: %s' % msg)


collectd.register_config(configure_callback)
collectd.register_read(read_callback)
