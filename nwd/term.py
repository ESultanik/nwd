import time

from .notify import Notifier


class TerminalNotifier(Notifier):
    def notify(self):
        print(f"\a\n\nProcess {self.pid} finished at {time.ctime(self.end_time)}\n")
