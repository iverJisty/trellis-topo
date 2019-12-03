#!/usr/bin/env python

import argparse
import json
from collections import OrderedDict

LEAF_BASE_ID = 204
SPINE_BASE_ID = 226


class LinkConfigGenerator():

    def __init__(self, nleaf, nspine, bandwidth, device_id_prefix):
        self.nleaf = nleaf
        self.nspine = nspine
        self.bandwidth = bandwidth
        self.device_id_prefix = device_id_prefix

    def generate_json(self):
        root = OrderedDict()
        root['links'] = OrderedDict()

        spine_port_idx = 1
        for leaf_idx in range(self.nleaf):
            leaf_port_idx = 1
            for spine_idx in range(self.nspine):
                leaf_id = LEAF_BASE_ID + leaf_idx
                spine_id = SPINE_BASE_ID + spine_idx
                link = '%s:%s/%d-%s:%s/%d' % \
                    (self.device_id_prefix, leaf_id, leaf_port_idx,
                     self.device_id_prefix, spine_id, spine_port_idx)
                root['links'][link] = OrderedDict()
                root['links'][link]['basic'] = OrderedDict()
                root['links'][link]['basic']['bandwidth'] = self.bandwidth
		leaf_port_idx += 1
            spine_port_idx += 1

        return json.dumps(root, indent=4)


def main(args):
    generator = LinkConfigGenerator(
        args.nleaf, args.nspine, args.bandwidth, args.device_prefix)
    json_data = generator.generate_json()

    if args.output is not None:
        with open(args.output, 'w') as output_file:
            output_file.write(json_data)
    else:
        print(json_data)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description='Link config generator for Trellis topology')
    parser.add_argument('--nleaf', help='Number of leaf switches',
                        type=int, default=2)
    parser.add_argument('--nspine', help='Number of spine switches',
                        type=int, default=2)
    parser.add_argument('--bandwidth', help='Link bandwidth capacity in Mbps',
                        type=int, required=True)
    parser.add_argument('--device-prefix', help='Prefix of device ID',
                        type=str, default='device:bmv2')
    parser.add_argument('-o', '--output', help='Write output to file')
    args = parser.parse_args()

    main(args)

