import os
import pwd
import glob
import time

from . import config


def active_users(tty_conf):
    """
    Return list of active users which are not in whitelist
    :param tty_conf: TtyConfiguration instance
    :return: list of active user names
    """
    assert isinstance(tty_conf, config.TTYConfiguration)

    result = []
    if not tty_conf.enabled:
        return result

    for pts_name in glob.glob("/dev/pts/*"):
        st = os.stat(pts_name)
        uname = pwd.getpwuid(st.st_uid).pw_name
        if uname in tty_conf.whitelist:
            continue
        if uname in result:
            continue
        idle_time = time.time() - st.st_atime
        if idle_time < tty_conf.idle_seconds:
            result.append(uname)
    return result
