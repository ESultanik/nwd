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
        notify('nwd', f"{self.name} finished!", f"Process {self.pid} finished at {time.ctime(self.end_time)}")
