import sys
import time

from .notify import Notifier

if sys.platform.startswith('darwin'):
    from .osx import notify
elif sys.platform == 'win32' or sys.platform == 'cygwin':
    from .windows import notify
else:
    from .gtk import notify


class DesktopNotifier(Notifier):
    def notify(self):
        message = f"Process {self.pid} finished at {time.ctime(self.end_time)}"
        if self.exitcode is not None:
            message = f"{message} with exit code {self.exitcode}."
        notify('nwd', f"{self.name} finished!", message)
