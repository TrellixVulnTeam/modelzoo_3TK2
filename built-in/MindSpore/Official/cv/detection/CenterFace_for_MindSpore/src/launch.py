# Copyright 2020 Huawei Technologies Co., Ltd
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
# http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
# ============================================================================
"""auto generate rank table and export envs"""

import sys
import subprocess
import os
import socket
import json
from argparse import ArgumentParser, REMAINDER

def parse_args():
    parser = ArgumentParser(description="mindspore distributed training launch "
                                        "helper utilty that will spawn up "
                                        "multiple distributed processes")

    parser.add_argument("--nproc_per_node", type=int, default=1,
                        help="The number of processes to launch on each node, "
                             "for D training, this is recommended to be set "
                             "to the number of D in your system so that "
                             "each process can be bound to a single D.")
    parser.add_argument("--visible_devices", type=str, default="0,1,2,3,4,5,6,7",
                        help="will use the visible devices sequentially")
    parser.add_argument("--env_sh", type=str, default="",
                        help="env for 1p")
    parser.add_argument("--server_id", type=str, default="",
                        help="server ip")

    # positional
    parser.add_argument("training_script", type=str,
                        help="The full path to the single D training "
                             "program/script to be launched in parallel, "
                             "followed by all the arguments for the "
                             "training script")

    # device mode
    parser.add_argument("--device", type=str, default="A+K")

    # task_set, to impove cpu utilization for multi-npu(e.g., 8P) training
    parser.add_argument("--task_set", type=bool, default=False)
    parser.add_argument("--task_set_core", type=int, default=24)

    # ranktable file
    parser.add_argument("--table_fn", type=str, default="",
                        help="The ranktable file path, if not set, "
                             "we will auto-generate a ranktable for user")

    # rest from the training program
    parser.add_argument('training_script_args', nargs=REMAINDER)

    return parser.parse_args()


def main():
    args = parse_args()
    print('args:{}'.format(args))
    visible_devices = args.visible_devices.split(',')
    assert len(visible_devices) >= args.nproc_per_node
    print('visible_devices:{}'.format(visible_devices))
    if(args.server_id == ''):
        print('pleaser input server ip!!!')
        exit(0)
    print('server_id:{}'.format(args.server_id))
    hccn_configs = open('/etc/hccn.conf', 'r').readlines()
    device_ips = {}
    for hccn_item in hccn_configs:
        hccn_item = hccn_item.strip()
        if hccn_item.startswith('address_'):
            device_id, device_ip = hccn_item.split('=')
            device_id = device_id.split('_')[1]
            device_ips[device_id] = device_ip
            print('device_id:{}, device_ip:{}'.format(device_id, device_ip))
    hccn_table = {}
    if args.device == 'A+K':
        hccn_table['board_id'] = '0x002f'
    else:
        hccn_table['board_id'] = '0x0000'
    hccn_table['chip_info'] = '910'
    hccn_table['deploy_mode'] = 'lab'
    hccn_table['group_count'] = '1'
    hccn_table['group_list'] = []
    instance_list = []
    usable_dev = ''
    for instance_id in range(args.nproc_per_node):
        instance = {}
        instance['devices'] = []
        device_id = visible_devices[instance_id]
        device_ip = device_ips[device_id]
        usable_dev += str(device_id)
        instance['devices'].append({
            'device_id': device_id,
            'device_ip': device_ip,
        })
        instance['rank_id'] = str(instance_id)
        instance['server_id'] = args.server_id
        instance_list.append(instance)
    hccn_table['group_list'].append({
        'device_num': str(args.nproc_per_node),
        'server_num': '1',
        'group_name': '',
        'instance_count': str(args.nproc_per_node),
        'instance_list': instance_list,
    })
    hccn_table['para_plane_nic_location'] = 'device'
    hccn_table['para_plane_nic_name'] = []
    for instance_id in range(args.nproc_per_node):
        eth_id = visible_devices[instance_id]
        hccn_table['para_plane_nic_name'].append('eth{}'.format(eth_id))
    hccn_table['para_plane_nic_num'] = str(args.nproc_per_node)
    hccn_table['status'] = 'completed'

    if args.table_fn is "":
        table_fn = os.path.join(os.getcwd(), 'rank_table_{}p_{}_{}.json'.format(args.nproc_per_node, usable_dev, args.server_id))
        with open(table_fn, 'w') as table_fp:
            json.dump(hccn_table, table_fp, indent=4)
    else:
        table_fn = args.table_fn

    # world size in terms of number of processes
    dist_group_size = args.nproc_per_node

    for rank in range(0, args.nproc_per_node):
        rank_id = rank
        device_id = visible_devices[rank]
        device_root_fn = os.path.join(os.getcwd(), 'device{}'.format(device_id)) #format(rank_id))
        rank_process = ''
        if args.nproc_per_node > 1:
            rank_process += 'export RANK_TABLE_FILE={} && '.format(table_fn)
        if args.task_set:
            left = int(device_id) * args.task_set_core
            right = left + args.task_set_core - 1
            rank_process += 'export RANK_SIZE={} && source {} && export RANK_ID={} && export DEVICE_ID={} && rm -rf {} && mkdir {} && cd {} && taskset -c {}-{} python {} '.format(args.nproc_per_node, args.env_sh, rank_id, device_id, device_root_fn, device_root_fn, device_root_fn, left, right, args.training_script)
        else:
            rank_process += 'export RANK_SIZE={} && source {} && export RANK_ID={} && export DEVICE_ID={} && rm -rf {} && mkdir {} && cd {} && python {} '.format(args.nproc_per_node, args.env_sh, rank_id, device_id, device_root_fn, device_root_fn, device_root_fn, args.training_script)
        rank_process += ' '.join(args.training_script_args) + ' >log{}.log 2>&1 &'.format(rank_id)
        os.system(rank_process)

if __name__ == "__main__":
    main()
