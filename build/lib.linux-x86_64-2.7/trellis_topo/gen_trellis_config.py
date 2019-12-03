#!/usr/bin/env python

import argparse
import json
from collections import OrderedDict

LEAF_BASE_ID = 204
SPINE_BASE_ID = 226
VLAN_UNTAGGED_BASE_ID = 10


class TrellisConfigGenerator():

    def __init__(self, nleaf, nspine, nhost, device_id_prefix):
        self.nleaf = nleaf
        self.nspine = nspine
        self.nhost = nhost
	self.device_id_prefix = device_id_prefix

    def generate_json(self):
        root = OrderedDict()
        root['ports'] = OrderedDict()
        root['devices'] = OrderedDict()

        # Interfaces config
        for leaf_idx in range(self.nleaf):
            for host_idx in range(self.nhost):
                # Assume leaf device use port 1..NUM_SPINE to connect spine
                # Ports start from NUM_SPINE+1 are connect to host
                leaf_id = LEAF_BASE_ID + leaf_idx
                port = '%s:%s/%d' % (self.device_id_prefix, leaf_id, self.nspine + 1 + host_idx)
                root['ports'][port] = OrderedDict()
                root['ports'][port]["interfaces"] = []

                interface = OrderedDict()
                interface["name"] = 'h%s' % (leaf_idx * self.nhost + host_idx + 1)  # start from h1
                interface["ips"] = ['10.0.%d.254/24' % (leaf_idx + 2)]  # start from 10.0.2.254/24
                interface["vlan-untagged"] = VLAN_UNTAGGED_BASE_ID * (leaf_idx + 1)  # 10, 20, 30 ...   

                root['ports'][port]["interfaces"].append(interface)

        # Segment Routing config
        for leaf_idx in range(self.nleaf):
            leaf_id = LEAF_BASE_ID + leaf_idx
            device_id = '%s:%s' % (self.device_id_prefix, leaf_id)
            root['devices'][device_id] = OrderedDict()
            sr_config = root['devices'][device_id]['segmentrouting'] = OrderedDict()

            sr_config['name'] = 's%d' % (leaf_id)
            sr_config['ipv4NodeSid'] = leaf_id
            sr_config['ipv4Loopback'] = '192.168.0.%d' % (leaf_id)
            sr_config['ipv6NodeSid'] = leaf_id + 10
            sr_config['ipv6Loopback'] = '2000::c0a8:%s' % (str(leaf_id).zfill(4))
            sr_config['routerMac'] = '00:00:00:00:%s' % \
                (':'.join(s.encode('hex') for s in str(leaf_id).zfill(4).decode('hex')))
            sr_config['isEdgeRouter'] = True
            sr_config['adjacencySids'] = []

        for spine_idx in range(self.nspine):
            spine_id = SPINE_BASE_ID + spine_idx
            device_id = '%s:%s' % (self.device_id_prefix, spine_id)
            root['devices'][device_id] = OrderedDict()
            sr_config = root['devices'][device_id]['segmentrouting'] = OrderedDict()

            sr_config['name'] = 's%d' % (spine_id)
            sr_config['ipv4NodeSid'] = spine_id
            sr_config['ipv4Loopback'] = '192.168.0.%d' % (spine_id)
            sr_config['ipv6NodeSid'] = spine_id + 10
            sr_config['ipv6Loopback'] = '2000::c0a8:%s' % (str(spine_id).zfill(4))
            sr_config['routerMac'] = '00:00:00:00:%s' % \
                (':'.join(s.encode('hex') for s in str(spine_id).zfill(4).decode('hex')))
            sr_config['isEdgeRouter'] = False
            sr_config['adjacencySids'] = []

        return json.dumps(root, indent=4)


def main(args):
    generator = TrellisConfigGenerator(args.nleaf, args.nspine, args.nhost, args.device_prefix)
    json_data = generator.generate_json()

    if args.output is not None:
        with open(args.output, 'w') as output_file:
            output_file.write(json_data)
    else:
        print(json_data)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description='Trellis config generator')
    parser.add_argument('--nleaf', help='Number of leaf switches',
                        type=int, default=2)
    parser.add_argument('--nspine', help='Number of spine switches',
                        type=int, default=2)
    parser.add_argument('--nhost', help='Number of hosts for each leaf switch',
                        type=int, default=2)
    parser.add_argument('--device-prefix', help='Prefix of device ID',
                        type=str, default='device:bmv2')
    parser.add_argument('-o', '--output', help='Write output to file')
    args = parser.parse_args()

    main(args)


