import sys
import time

from .notify import Notifier


class TerminalNotifier(Notifier):
    def notify(self):
        sys.stdout.write(f"\a\n\nNWD: Process {self.pid} finished at {time.ctime(self.end_time)}")
        if self.exitcode is not None:
            sys.stdout.write(f" with exit code {self.exitcode}")
        sys.stdout.write('\n\n')
