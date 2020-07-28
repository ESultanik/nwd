from enum import Enum
import json
import os
from pathlib import Path
import sys
import time

from typing import Dict, Iterable, List, Optional, Union

import psutil

from .daemon import spawn_daemon

PID_DIR = os.path.join(str(Path.home()), '.nwd')
os.makedirs(PID_DIR, exist_ok=True)


class Status(Enum):
    NOT_STARTED = 0
    MONITORING = 1
    NOTIFYING = 2
    NOTIFIED = 3
    FAILED = 4


def cleanup():
    for notifier in get_notifiers():
        status = notifier.status
        if status == Status.NOTIFIED or status == Status.FAILED:
            os.unlink(notifier.pidfile)
            yield notifier, status


class Notifier:
    def __init__(self, pid: int, daemon_pid: Optional[int] = None, stdout=None, stderr=None):
        self.pidfile = None
        self.pid = pid
        self._daemon_pid = None
        self.daemon_pid = daemon_pid
        self.stdout = stdout
        self.stderr = stderr

    @property
    def daemon_pid(self) -> int:
        return self._daemon_pid

    @daemon_pid.setter
    def daemon_pid(self, pid: int):
        if self._daemon_pid is not None:
            if self._daemon_pid == pid:
                return
            raise Exception(f"Cannot set the daemon PID to {pid} because it is already set to {self._daemon_pid}")
        self._daemon_pid = pid
        if pid is not None:
            self.pidfile = os.path.join(PID_DIR, str(pid))

    def _raw_status(self) -> Dict[str, Union[int, str, List[str], Optional[float]]]:
        if self.pidfile is None or not os.path.exists(self.pidfile):
            return {
                'pid': self.pid,
                'name': f"Process {self.pid}",
                'commandline': [],
                'exitcode': None,
                'started': None,
                'finished': None,
                'status': Status.NOT_STARTED.name
            }
        with open(self.pidfile) as f:
            return json.load(f)

    def _save_status(self, **kwargs):
        existing_status = self._raw_status()
        existing_status.update(kwargs)
        with open(self.pidfile, 'w') as f:
            json.dump(existing_status, f)

    @property
    def status(self) -> Status:
        s = Status.__members__[self._raw_status()['status']]
        try:
            if s != Status.NOTIFIED and not psutil.Process(self.daemon_pid).is_running():
                s = Status.FAILED
        except psutil.NoSuchProcess:
            if s != Status.NOTIFIED:
                s = Status.FAILED
        return s

    @status.setter
    def status(self, new_status: Status):
        self._save_status(status=new_status.name)

    @property
    def name(self) -> str:
        return self._raw_status()['name']

    @property
    def commandline(self) -> List[str]:
        return self._raw_status()['commandline']

    @property
    def exitcode(self) -> Optional[int]:
        return self._raw_status()['exitcode']

    @exitcode.setter
    def exitcode(self, new_exitcode: int):
        self._save_status(exitcode=new_exitcode)

    def notify(self):
        raise NotImplementedError('Subclasses of Notifier must implement the notify() function')

    @property
    def start_time(self) -> float:
        return self._raw_status()['started']

    @property
    def end_time(self) -> float:
        return self._raw_status()['finished']

    def terminate(self):
        status = self.status
        if status == Status.MONITORING or status == Status.NOTIFYING:
            psutil.wait_procs([psutil.Process(self.daemon_pid)])
        os.unlink(self.pidfile)

    def start(self, block=False) -> int:
        if self.daemon_pid is not None:
            return self.daemon_pid
        if not block:
            child_pid = spawn_daemon()
            if child_pid > 0:
                # we are in the parent process
                self.daemon_pid = child_pid
                return child_pid

        # We are now executing in the daemon process
        self.daemon_pid = os.getpid()
        self.status = Status.MONITORING
        # Maybe the process is already finished?
        process = psutil.Process(self.pid)
        if process.is_running():
            self._save_status(
                name=process.name(),
                commandline=process.cmdline(),
                started=process.create_time()
            )
            exitcode = process.wait()
            if exitcode is not None:
                self._save_status(
                    exitcode=process.wait(),
                    finished=time.time()
                )
            else:
                self._save_status(
                    finished=time.time()
                )
        else:
            self._save_status(
                finished=time.time()
            )
        self.status = Status.NOTIFYING
        self.notify()
        self.status = Status.NOTIFIED
        sys.exit(os.EX_OK)


def get_notifiers(for_pid: Optional[int] = None) -> Iterable[Notifier]:
    for pid in os.listdir(PID_DIR):
        path = os.path.join(PID_DIR, pid)
        if not os.path.isfile(path):
            continue
        try:
            pid = int(pid)
        except ValueError:
            continue
        with open(path) as f:
            proc_pid: int = json.load(f)['pid']
        if for_pid is None or for_pid == proc_pid:
            yield Notifier(pid=proc_pid, daemon_pid=pid)
