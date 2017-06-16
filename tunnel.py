#!/usr/bin/env python
# -*- coding:utf-8 -*-
import sys
import os
from sshtunnel import SSHTunnelForwarder
import time
import yaml
from typing import List,Tuple,Dict

import logging
logger = logging.getLogger(__file__)
logger.setLevel(logging.INFO)
logger.addHandler(logging.StreamHandler())

app_dir = os.path.abspath(os.path.realpath(os.path.dirname(__file__)))
config_load_path = ['', app_dir, os.path.join(app_dir,'conf')]


def find_config_file(file_name:str) -> str:
    file_path = file_name
    for config_dir in config_load_path:
        file_path = os.path.realpath(os.path.join(config_dir,file_name))
        if os.path.isfile(file_path):
            return file_path

    raise IOError(f'cannot find config file {file_name}')


def load_config(file_name:str) -> Dict:
    file_path = find_config_file(file_name)
    with open(file_path) as f:
        return yaml.load(f)


class LocalTunnel:
    def __init__(self, ssh_expr:str, fwd_exprs:List[str], ssh_pkey:str=None):
        self.fwd_exprs = fwd_exprs
        self.ssh_expr = ssh_expr
        self.ssh_pkey = ssh_pkey
        self._param = self._create_forwarder_param(ssh_expr, fwd_exprs, ssh_pkey)
        self._forwarder = SSHTunnelForwarder(**self._param)

    def _create_forwarder_param(self, ssh_expr:str, fwd_exprs:List[str], ssh_pkey:str):
        local_binds = []
        remote_binds = []

        logger.info(f'setting up local tunnels via {self.ssh_expr}')

        for fwd_expr in fwd_exprs:
            local_host, local_port, remote_host, remote_port = fwd_expr.split(':')
            local_host = local_host or '127.0.0.1'
            local_binds.append( (local_host, int(local_port)) )
            remote_binds.append( (remote_host, int(remote_port)) )
            logger.info(f'    add {local_host}:{local_port} -> {remote_host}:{remote_port}')

        param = {
            'local_bind_addresses': local_binds,
            'remote_bind_addresses': remote_binds,
        }
        if '@' in ssh_expr:
            param['ssh_username'], param['ssh_host'] = ssh_expr.split('@')
        else:
            param['ssh_host'] = ssh_expr
        if ssh_pkey:
            param['ssh_pkey'] = os.path.expanduser(ssh_pkey)
        return param

    def start(self):
        self._forwarder.start()

    def stop(self):
        self._forwarder.stop()


def accept_conf(conf:Dict) -> LocalTunnel:
    ssh_expr = conf['host']
    ssh_pkey = conf.get('key')
    local_fwds = conf.get('locals')
    return LocalTunnel(ssh_expr, local_fwds, ssh_pkey)


def main(args:List[str]):
    local_tunnels = []  # type: List[LocalTunnel]

    conf_files = args[:]
    for conf_file in conf_files:
        conf_list = load_config(conf_file)
        if not isinstance(conf_list, list):
            conf_list = [conf_list]
        for conf in conf_list:
            local_tunnels.append(accept_conf(conf))

    try:
        for tun in local_tunnels:
            logger.info(f'start tunnel {tun.ssh_expr}')
            tun.start()

        logger.info('started')

        # wait forever
        while True:
            time.sleep(60)

    finally:
        for tun in local_tunnels:
            try:
                tun.stop()
            except:
                logger.exception('failed to stop server '+ str(tun))


if __name__ == '__main__':
    main(sys.argv[1:])
