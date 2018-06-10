#!/usr/bin/python

import os
import sys
import argparse
sys.path.append('..')

if 'ONOS_ROOT' not in os.environ:
    print "Environment var $ONOS_ROOT not set"
    exit()
else:
    ONOS_ROOT = os.environ["ONOS_ROOT"]
    sys.path.append(ONOS_ROOT + "/tools/dev/mininet")

from mininet.topo import Topo
from mininet.net import Mininet
from mininet.cli import CLI
from mininet.log import setLogLevel
from mininet.node import Host, RemoteController
from routinglib import RoutedHost
from bmv2 import ONOSBmv2Switch

PIPECONF_ID = 'org.onosproject.pipelines.fabric'

LEAF_START_INDEX = 204
SPINE_START_INDEX = 226
LEAF_GRPC_PORT_START = 55204
SPINE_GRPC_PORT_START = 55226

nleaf = 2
nspine = 2
nhost = 2

class Trellis( Topo ):
    "Trellis basic topology"

    def __init__( self, *args, **kwargs ):
        Topo.__init__( self, *args, **kwargs )

        leafSwitches = []
        spineSwitches = []

        for n in range(nleaf):
            self.addSwitch("s" + str(LEAF_START_INDEX + n), 
                cls=ONOSBmv2Switch, deviceId=str(LEAF_START_INDEX + n), grpcport=LEAF_GRPC_PORT_START + n, 
                pipeconf=PIPECONF_ID, portcfg=True)
            leafSwitches.append("s" + str(LEAF_START_INDEX + n))

        for n in range(nspine):
            self.addSwitch("s" + str(SPINE_START_INDEX + n), 
                cls=ONOSBmv2Switch, deviceId=str(SPINE_START_INDEX + n), grpcport=SPINE_GRPC_PORT_START + n, 
                pipeconf=PIPECONF_ID, portcfg=True)
            spineSwitches.append("s" + str(SPINE_START_INDEX + n))

        for leaf in leafSwitches:
            for spine in spineSwitches:
                self.addLink(leaf, spine)

        # NOTE avoid using t=10.0.1.0/24 which is the default subnet of quaggas
        # NOTE avoid using 00:00:00:00:00:xx which is the default mac of host behind upstream router
        # IPv4 Hosts
        for m in range(nleaf):
            for n in range(nhost):
                mac = "00:aa:00:00:00:" + str(m*nhost+n+1).zfill(2)
                ip = "10.0." + str(m+2) + "." + str(n+1) + "/24"
                gateway = "10.0." + str(m+2) + ".254"
                host = self.addHost("h" + str(m*nhost+n+1), cls=RoutedHost, mac=mac, ips=[ip], gateway=gateway)
                self.addLink("s" + str(LEAF_START_INDEX + m), host)

topos = { 'trellis' : Trellis }

def main(args):
    topo = Trellis()
    controller = RemoteController('c0', ip=args.onos_ip)

    net = Mininet(topo=topo, controller=None)
    net.addController(controller)

    net.start()
    CLI(net)
    net.stop()

if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description='BMv2 mininet demo script (2 by 2 fabric)')
    parser.add_argument('--onos-ip', help='ONOS-BMv2 controller IP address',
                        type=str, action="store", required=True)
    parser.add_argument('--nleaf', help='Number of leaf switches',
                        type=int, action="store", default=2, required=False)
    parser.add_argument('--nspine', help='Number of spine switches',
                        type=int, action="store", default=2, required=False)
    parser.add_argument('--nhost', help='Number of host for each leaf switch',
                    type=int, action="store", default=2, required=False)
    args = parser.parse_args()
    setLogLevel('debug')

    nleaf = args.nleaf
    nspine = args.nspine
    nhost = args.nhost

    main(args)
