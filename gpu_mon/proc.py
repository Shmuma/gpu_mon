"""
Get list of processes IDs with their names which open given files
"""
import logging
import collections
import subprocess
import re

log = logging.getLogger("proc")

ProcInfo = collections.namedtuple('ProcInfo', field_names=['file_name', 'pid', 'name'])


def _parse_fuser_output(data_str):
    result = []
    cur_fname = None

    for l in data_str.strip().split('\n'):
        parts = re.split(r'\s+', l)
        if not parts:
            continue
        if parts[0].endswith(':'):
            cur_fname = parts.pop(0)[:-1]
        if cur_fname is None:
            continue
        pid = int(parts[1])
        proc_name = parts[3]
        result.append(ProcInfo(file_name=cur_fname, pid=pid, name=proc_name))

    return result


def get_processes(file_names):
    """
    From list of files return list of processes which opens those files
    :param file_names: list of file names to check
    :return: list of ProcInfo objects or None if an error occured
    """
    try:
        out = subprocess.check_output(['fuser', '-av'] + list(file_names), stderr=subprocess.STDOUT)
    except Exception as e:
        log.error("Error occured during fuser: %s", e)
        return None
    return _parse_fuser_output(str(out, encoding='utf-8'))

