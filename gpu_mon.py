#!/usr/bin/env python
import argparse
import logging

log = logging.getLogger("gpu_mon")

DEFAULT_CONFIG = "~/.config/gpu_mon.conf"


if __name__ == "__main__":
    logging.basicConfig(format="%(asctime)-15s %(levelname)s %(name)-14s %(message)s", level=logging.INFO)

    parser = argparse.ArgumentParser()
    parser.add_argument("-c", "--conf", default=DEFAULT_CONFIG,
                        help="Configuration file to use, default=" + DEFAULT_CONFIG)
    args = parser.parse_args()


    pass
