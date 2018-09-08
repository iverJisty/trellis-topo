#!/usr/bin/env python

from mininet.topo import Topo
from mininet.net import Mininet
from mininet.link import TCLink
from mininet.cli import CLI
from mininet.node import RemoteController
from mininet.log import setLogLevel
from routinglib import RoutedHost
from bmv2 import ONOSBmv2Switch
import argparse

LEAF_BASE_ID = 204
SPINE_BASE_ID = 226
LEAF_BASE_GRPC_PORT = 55204
SPINE_BASE_GRPC_PORT = 55226


class Trellis(Topo):
    "Trellis basic topology"

    def __init__(self, nleaf, nspine, nhost, bandwidth, pipeconf_id):
        Topo.__init__(self)

        leafSwitches = []
        spineSwitches = []

        # Add switches
        for leaf_idx in range(nleaf):
            leaf_id = LEAF_BASE_ID + leaf_idx
            self.addSwitch('s%d' % (leaf_id),
                           cls=ONOSBmv2Switch,
                           grpcport=LEAF_BASE_GRPC_PORT + leaf_idx,
                           pipeconf=pipeconf_id,
                           portcfg=True)
            leafSwitches.append('s%d' % (leaf_id))

        for spine_idx in range(nspine):
            spine_id = SPINE_BASE_ID + spine_idx
            self.addSwitch('s%d' % (spine_id),
                           cls=ONOSBmv2Switch,
                           grpcport=SPINE_BASE_GRPC_PORT + spine_idx,
                           pipeconf=pipeconf_id,
                           portcfg=True)
            spineSwitches.append('s%d' % (spine_id))

        # Add switch links
        for leaf in leafSwitches:
            for spine in spineSwitches:
                if bandwidth is not None:
                    self.addLink(leaf, spine, bw=bandwidth)
                else:
                    self.addLink(leaf, spine)

        # NOTE avoid using 10.0.1.0/24 which is the default subnet of quaggas
        # NOTE avoid using 00:00:00:00:00:xx which is the default mac of host behind upstream router
        # Add IPv4 hosts
        for leaf_idx in range(nleaf):
            for host_idx in range(nhost):
                leaf_id = LEAF_BASE_ID + leaf_idx
                host_id = leaf_idx * nhost + host_idx + 1
                mac = '00:aa:00:00:00:%s' % (str(host_id).zfill(2))
                ip = '10.0.%d.%d/24' % (leaf_idx + 2, host_idx + 1)  # start from 10.0.2.1/24
                gateway = '10.0.%d.254' % (leaf_idx + 2)  # start from 10.0.2.254

                host = self.addHost('h%d' % (host_id), cls=RoutedHost, mac=mac, ips=[ip], gateway=gateway)
                self.addLink('s%d' % (leaf_id), host)


topos = {'trellis': Trellis}


def main(args):
    topo = Trellis(args.nleaf, args.nspine, args.nhost, args.bandwidth, args.pipeconf)
    controller = RemoteController('c0', ip=args.onos_ip)

    net = Mininet(topo=topo, link=TCLink, controller=None)
    net.addController(controller)

    net.start()
    CLI(net)
    net.stop()


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description='Mininet script for Trellis topology with BMv2 switch')
    parser.add_argument('--onos-ip', help='ONOS controller IP address',
                        type=str, required=True)
    parser.add_argument('--nleaf', help='Number of leaf switches',
                        type=int, default=2)
    parser.add_argument('--nspine', help='Number of spine switches',
                        type=int, default=2)
    parser.add_argument('--nhost', help='Number of hosts for each leaf switch',
                        type=int, default=2)
    parser.add_argument('--bandwidth', help='Link bandwidth capacity in Mbps',
                        type=float)
    parser.add_argument('--pipeconf', help='Pipeconf Id to be deployed on device',
                        type=str, default='org.onosproject.pipelines.fabric')
    args = parser.parse_args()

    setLogLevel('debug')

    main(args)

