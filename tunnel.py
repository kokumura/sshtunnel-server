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


class LocalTunnel:
    def __init__(self, ssh_expr:str, fwd_exprs:List[str], ssh_pkey:str=None, default_local_addr=None):
        self.fwd_exprs = fwd_exprs
        self.ssh_expr = ssh_expr
        self.ssh_pkey = ssh_pkey
        self.default_local_addr = default_local_addr
        self._param = self._create_forwarder_param(ssh_expr, fwd_exprs, ssh_pkey)
        self._forwarder = SSHTunnelForwarder(**self._param)

    def _create_forwarder_param(self, ssh_expr:str, fwd_exprs:List[str], ssh_pkey:str):
        local_binds = []
        remote_binds = []

        logger.info(f'setting up local tunnels via `{self.ssh_expr}`')

        for fwd_expr in fwd_exprs:
            local_host, local_port, remote_host, remote_port = fwd_expr.split(':')
            local_host = local_host or self.default_local_addr or '127.0.0.1'
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


def accept_conf(conf:Dict, default_local_addr) -> LocalTunnel:
    ssh_expr = conf['host']
    ssh_pkey = conf.get('key')
    local_fwds = conf.get('locals')
    return LocalTunnel(ssh_expr, local_fwds, ssh_pkey, default_local_addr)


def load_config(file_path:str) -> Dict:
    with open(os.path.expanduser(file_path)) as f:
        return yaml.load(f)


def parse_args(args):
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument('--addr', help='default local bind address (DEFAULT: 127.0.0.1)', type=str, default='127.0.0.1')
    parser.add_argument('--exec', help='execute command', type=str)
    parser.add_argument('--silent', help='be silent', action='store_true')
    parser.add_argument('conf_files', help='forward config files', type=str, nargs='+')
    return parser.parse_args(args)


def main(args):
    local_tunnels = []  # type: List[LocalTunnel]
    local_addr = args.addr
    conf_files = args.conf_files
    exec_command = args.exec

    if args.silent:
        logger.setLevel(logging.WARN)

    for conf_file in conf_files:
        conf_list = load_config(conf_file)
        if not isinstance(conf_list, list):
            conf_list = [conf_list]
        for conf in conf_list:
            local_tunnels.append(accept_conf(conf, default_local_addr=local_addr))

    try:
        for tun in local_tunnels:
            logger.info(f'starting tunnel `{tun.ssh_expr}`')
            tun.start()

        logger.info('started')

        if exec_command is None:
            # server mode: wait forever
            while True:
                time.sleep(60)

        else:
            import subprocess
            logger.info(f'execute {exec_command}')
            retcode = subprocess.check_call(exec_command, shell=True)
            exit(retcode)

    finally:
        for tun in local_tunnels:
            try:
                tun.stop()
            except:
                logger.exception(f'failed to stop server {str(tun)}')


if __name__ == '__main__':
    def configure_logger(logger):
        log_level = logging.INFO
        handler = logging.StreamHandler(sys.stderr)
        formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
        logger.addHandler(handler)
        handler.setLevel(log_level)
        handler.setFormatter(formatter)
        logger.setLevel(log_level)
    configure_logger(logger)
    main(parse_args(sys.argv[1:]))
