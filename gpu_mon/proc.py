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
        if not parts or len(parts) < 5:
            continue
        if parts[0].endswith(':'):
            cur_fname = parts[0][:-1]
        if cur_fname is None:
            continue
        pid = int(parts[2])
        proc_name = parts[4]
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
        args = ['fuser', '-av'] + list(files_to_ids.keys())
        out = subprocess.run(args, stderr=subprocess.STDOUT, stdout=subprocess.PIPE).stdout
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
        self._stop_everything()

    def check(self, gpus, processes, active_users):
        """
        Perform check for new observations got and modify started processes set accordingly
        :param gpus: list of GPUinfo for all GPUs
        :param processes: list of ProcInfo instances
        :param active_users: list of active users
        """
        self._check_running()

        # if there are some users active and we have anything running, stop, without even checking for idle
        if active_users:
            if self.started:
                self.log.info("Users %s become active, stop %d processes", active_users, len(self.started))
                self._stop_everything()
            return

        idle_gpus = {g.id for g in gpus}
        all_pids = {p.pid for p in self.started.values()}

        # if there are active non-our processes, stop matching gpu workers
        for proc in processes:
            assert isinstance(proc, ProcInfo)
            # is_our_pid is strict check
            if self.is_our_pid(proc.gpu_id, proc.pid):
                self.log.info("Our own pid in proc: %s", proc)
                idle_gpus.discard(proc.gpu_id)
                continue
            # if this proc.pid is in our pids, it cannot be preemptor
            if proc.pid in all_pids:
                continue
            if self.is_whitelist_proc_name(proc.gpu_id, proc.name):
                self.log.info("Whitelisted proc: %s", proc)
                continue
            idle_gpus.discard(proc.gpu_id)
            running_ids = self._running_on_gpu(proc.gpu_id)
            if running_ids:
                self.log.info("Stop %d processes preempted by proc %s", len(running_ids), proc)
                for gpu_id in running_ids:
                    self._stop_by_id(gpu_id)

        # no gpus, no actions
        if not idle_gpus:
            return

        # in case we have idle gpus, try to start something on them
        self.log.info("%d gpus are idle", len(idle_gpus))

        # ALL process configuration has preference
        if len(idle_gpus) == len(gpus):
            proc_conf = self.conf.process_config(None)
            if proc_conf:
                r = self._start_by_conf(proc_conf)
                if r is not None:
                    self.started[None] = r
                idle_gpus.clear()

        for gpu_id in idle_gpus:
            proc_conf = self.conf.process_config(gpu_id)
            if proc_conf:
                r = self._start_by_conf(proc_conf)
                if r is not None:
                    self.started[gpu_id] = r
            else:
                self.log.warning("GPU %d is idle, but we have no process config, ignored", gpu_id)

    def _check_running(self):
        """
        Check running processes and cleanup dead
        """
        dead = []
        for gpu_id, p in self.started.items():
            p.poll()
            if p.returncode is None:
                continue
            p.wait(timeout=1)
            self.log.info("Process for %s is terminated", gpu.format_gpu_id(gpu_id))
            dead.append(gpu_id)
        for d in dead:
            self.started.pop(d)

    def _start_by_conf(self, proc_conf):
        """
        Start subprocess using ProcConfiguration object
        :param proc_conf: 
        :return: Popen object instance
        """
        assert isinstance(proc_conf, config.ProcessConfiguration)

        args = list(proc_conf.cmd.split(' '))
        self.log.info("Starting: %s on %s", proc_conf.cmd, gpu.format_gpu_id(proc_conf.gpu_indices))
        if proc_conf.gpu_indices is not None:
            env = {"CUDA_VISIBLE_DEVICES": ",".join(map(str, sorted(proc_conf.gpu_indices)))}
        else:
            env = None
        p = subprocess.Popen(args, cwd=proc_conf.dir, env=env)
        return p

    def _running_on_gpu(self, gpu_id):
        """
        Return list of GPU ids for processes occuping this gpu. 
        :param gpu_id: GPU id or None for all GPUs 
        :return: list of GPU ids 
        """
        if gpu_id is None:
            return list(self.started.keys())
        if None in self.started:
            return [None]
        if gpu_id not in self.started:
            return []
        return [gpu_id]

    def _stop_everything(self):
        if not self.started:
            return
        for gpu_id in self.started.keys():
            self.log.info("Stopping proc for %s", gpu.format_gpu_id(gpu_id))
            self._stop_by_id(gpu_id)

    def _stop_by_id(self, gpu_id):
        proc = self.started.pop(gpu_id, None)
        proc.kill()
        proc.wait()

    def is_our_pid(self, gpu_id, pid):
        """
        Check that this pid is from our process
        """
        for proc_gpu_id, proc in self.started.items():
            if proc_gpu_id == gpu_id and proc.pid == pid:
                return True
        return False

    def is_whitelist_proc_name(self, gpu_id, name):
        """
        Checks that this name is prefix of one of whitelisted processes
        """
        for conf in self.conf.gpus_conf:
            assert isinstance(conf, config.GPUConfiguration)
            if conf.gpu_indices is None or gpu_id in conf.gpu_indices:
                for wl in conf.ignore_programs:
                    if wl.startswith(name):
                        return True
        return False

