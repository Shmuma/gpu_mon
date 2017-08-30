"""
Get list of processes IDs with their names which open given files
"""
import logging
import collections
import subprocess
import re

from . import config
from . import gpu


log = logging.getLogger("proc")

ProcInfo = collections.namedtuple('ProcInfo', field_names=['file_name', 'gpu_id', 'pid', 'name'])


def _parse_fuser_output(data_str, file_to_gpu_id):
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
        result.append(ProcInfo(file_name=cur_fname, gpu_id=file_to_gpu_id[cur_fname], pid=pid, name=proc_name))

    return result


def get_processes(gpu_infos):
    """
    From list of files return list of processes which opens those files
    :param gpu_infos: list of detected GPUs
    :return: list of ProcInfo objects or None if an error occured
    """
    files_to_ids = {gpu.file_name: gpu.id for gpu in gpu_infos}
    try:
        out = subprocess.check_output(['fuser', '-av'] + list(files_to_ids.keys()), stderr=subprocess.STDOUT)
    except Exception as e:
        log.error("Error occured during fuser: %s", e)
        return None
    return _parse_fuser_output(str(out, encoding='utf-8'), files_to_ids)


class ProcessTracker:
    log = logging.getLogger("ProcessTracker")

    """
    It tracks started processes. Glue of the whole system
    """
    def __init__(self, conf):
        assert isinstance(conf, config.Configuration)
        self.conf = conf
        self.started = {}

    def close(self):
        """
        Kill all started processes and exit gracefully
        """
        pass

    def check(self, processes, active_users):
        """
        Perform check for new observations got and modify started processes set accordingly
        :param processes: list of ProcInfo instances
        :param active_users: list of active users
        """
        # TODO: check and cleanup dead processes
        # if there are some users active and we have anything running, stop
        if active_users and self.started:
            self.log.info("Users %s become active, stop %d processes", active_users, len(self.started))
            self._stop_everything()
            return

        # if there are active non-our processes, stop matching gpu workers
        for proc in processes:
            assert isinstance(proc, ProcInfo)
            if self.is_our_pid(proc.pid):
                self.log.info("Our own pid in proc: %s", proc)
                continue
            if self.is_whitelist_proc_name(proc.name):
                self.log.info("Whitelisted proc: %s", proc)
                continue
            running_keys = self._running_keys(proc.gpu_id)
            if running_keys:
                self.log.info("Stop %d processes preempted by proc %s", len(running_keys), proc)
                for gpu_id in running_keys:
                    self._stop_by_id(gpu_id)

    def _stop_everything(self):
        if not self.started:
            return
        for gpu_id, proc in self.started.items():
            self.log.info("Stopping proc for %s", gpu.format_gpu_id(gpu_id))
            proc.kill()
            proc.wait()

    def _stop_by_id(self, gpu_id):
        proc = self.started.pop(gpu_id, None)
        proc.kill()
        proc.wait()

    def is_our_pid(self, pid):
        """
        Check that this pid is from our process
        """
        for proc in self.started.values():
            if proc.pid == pid:
                return True
        return False

    def is_whitelist_proc_name(self, name):
        """
        Checks that this name is prefix of one of whitelisted processes
        """
        for wl in self.conf.gpus_conf.ignore_programs:
            if wl.startswith(name):
                return True
        return False

