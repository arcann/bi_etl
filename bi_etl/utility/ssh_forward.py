import random
import subprocess
import time
from configparser import ConfigParser

from bi_etl.bi_config_parser import BIConfigParser

import logging

log = logging.getLogger('etl.utils.ssh_forward')


def ssh_forward(
        host: str,
        user: str,
        server: str,
        server_port: int,
        local_port: int = None,
        wait: bool = False,
        ssh_path: str = None,
        seconds_wait_for_usage: int = 60):
    # Command line options documentation
    # https://man.openbsd.org/ssh
    if ssh_path is None:
        ssh_path = 'ssh'
    if local_port is None:
        local_port = random.randrange(10000, 60000)
    cmd = [
        ssh_path,
        '{user}@{host}'.format(user=user, host=host),
        '-L', '127.0.0.1:{local_port}:{server}:{server_port}'.format(
            local_port=local_port,
            server=server,
            server_port=server_port,
        ),
        '-o', 'ExitOnForwardFailure=yes',
        '-o', 'StrictHostKeyChecking=no',
        # Sleep 10 will give 10 seconds to connect before it shuts down.
        # It will not exit while the forward port is in use.
        # If this is the second forward to run it will exit after 10 seconds since it won't have
        # an active forward.
        'sleep', str(seconds_wait_for_usage),
    ]
    log.debug("Starting ssh")
    log.debug(' '.join(cmd))
    try:
        if wait:
            stdout = subprocess.PIPE
            stderr = subprocess.PIPE
        else:
            stdout = subprocess.DEVNULL
            stderr = subprocess.DEVNULL
        p = subprocess.Popen(cmd, stdout=stdout, stderr=stderr, universal_newlines=True)
        log.info("Started ssh as ppid {}".format(p.pid))
        if wait:
            outs, errs = p.communicate()
        else:
            time.sleep(0.25)
            outs = None
            errs = None
        rc = p.poll()
        if rc is not None:
            if rc != 0:
                if outs:
                    log.info(outs)
                if errs:
                    log.error(errs)
                log.error("ssh return code = {}".format(rc))
        else:
            log.info("ssh tunnel running OK with local_port = {}".format(local_port))

        return local_port

    except subprocess.CalledProcessError as e:
        log.error(e.stdout)
        log.error(e.stderr)
        raise e


def ssh_forward_using_config(config: ConfigParser, section='ssh', wait=False):
    host = config[section]['host']
    user = config[section]['user']
    server = config.get(section, 'server', fallback='localhost')
    server_port = config[section]['server_port']
    local_port = config[section].get('local_port', fallback=None)
    ssh_path = config[section].get('ssh_path', fallback=None)
    seconds_wait_for_usage = config[section].getint('seconds_wait_for_usage', fallback=60)
    local_port = ssh_forward(
        host=host,
        user=user,
        local_port=local_port,
        server=server,
        server_port=server_port,
        wait=wait,
        ssh_path=ssh_path,
        seconds_wait_for_usage=seconds_wait_for_usage,
    )
    seconds_wait_for_tunnel_start = config[section].getint('seconds_wait_for_tunnel_start', fallback=2)
    if seconds_wait_for_tunnel_start:
        time.sleep(seconds_wait_for_tunnel_start)

    return local_port


if __name__ == '__main__':
    my_config = BIConfigParser()
    my_config.read_config_ini()
    ssh_forward_using_config(my_config, wait=True)
