#!/usr/bin/env python
import time
import argparse
import logging

from gpu_mon import config
from gpu_mon import proc
from gpu_mon import gpu
from gpu_mon import tty


log = logging.getLogger("gpu_mon")

DEFAULT_CONFIG = "~/.config/gpu_mon.conf"


if __name__ == "__main__":
    logging.basicConfig(format="%(asctime)-15s %(levelname)s %(name)-14s %(message)s", level=logging.INFO)

    parser = argparse.ArgumentParser()
    parser.add_argument("-c", "--conf", default=DEFAULT_CONFIG,
                        help="Configuration file to use, default=" + DEFAULT_CONFIG)
    args = parser.parse_args()
    conf = config.Configuration.read(args.conf)

    gpus = gpu.detect_gpus()
    log.info("GPUs detected: ")
    for g in gpus:
        log.info(g)

    files = [g.file_name for g in gpus]

    try:
        while True:
            processes = proc.get_processes(files)
            for p in processes:
                log.info(p)
            active_users = tty.active_users(conf.tty_conf)
            for u in active_users:
                log.info(u)
            time.sleep(conf.interval_seconds)
    except KeyboardInterrupt:
        log.info("Interrupt received, exit gracefully")

    pass
