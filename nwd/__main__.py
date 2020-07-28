import argparse
from functools import partial
import os
import shlex
import subprocess
import sys
import tempfile
import time

from typing import List, Optional

import psutil

from .daemon import spawn_daemon
from .desktop import DesktopNotifier
from .email import EmailNotifier, get_email_credentials, prompt_and_save_email_credentials
from .tabular import draw_table
from .term import TerminalNotifier
from . import notify


class RunNotifier(notify.Notifier):
    def __init__(self, run_command, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.run_command = run_command

    def notify(self):
        os.system(self.run_command)


def main(argv: Optional[List[str]] = None):  # noqa: C901
    parser = argparse.ArgumentParser(description='Notify When Done (NWD). A tool for posting a desktop notification, '
                                                 'E-mail, or other alert when a process finishes.')
    parser.add_argument('PID', type=int, nargs='?', help='the process ID to monitor')
    parser.add_argument('--name', '-n', type=str, default=None,
                        help='specify the process by its name instead of its PID')
    parser.add_argument('--exec', '-e', type=str, default=None,
                        help='executes the given command creates a notification on its completion')
    parser.add_argument('--block', '-b', action='store_true', default=False,
                        help='block until the monitored process terminates')
    parser.add_argument('--list', '-l', action='store_true', default=False,
                        help='lists all pending and completed notifications')
    parser.add_argument('--delete', '-d', action='store_true', default=False,
                        help='cancels the pending notification for the process specified by its PID or by --name')
    parser.add_argument('--cleanup', '-c', action='store_true', default=False,
                        help='clean up stale output from --list')
    parser.add_argument('--mode', '-m', choices=['desktop', 'email', 'term'], default=None,
                        help='sets the notification method, where \'desktop\' (the default) is a desktop notification '
                             'popup, \'email\' sends an e-mail, and \'term\' prints a message to the terminal')
    parser.add_argument('--run', '-r', type=str, default=None, help='run the given command when the process completes')
    parser.add_argument('--email-credentials', action='store_true', default=False,
                        help='prompt for the e-mail credentials with which to send alerts and offer to save them to '
                             'the system keychain')

    if argv is None:
        argv = sys.argv

    args = parser.parse_args(argv[1:])

    num_run_args = sum(map(bool, (args.PID, args.name, args.exec)))
    if num_run_args > 1:
        parser.print_help(sys.stderr)
        sys.stderr.write('\nYou may only specify at most one of PID, --name, and --exec\n')
        sys.exit(1)
    elif num_run_args == 0 and not (args.cleanup or args.list or args.email_credentials):
        parser.print_help(sys.stderr)
        sys.exit(1)

    if args.delete:
        if not args.PID and args.name is None:
            parser.print_help(sys.stderr)
            sys.stderr.write('\nYou must specify either a PID or a --name when using --delete\n')
            sys.exit(1)
        elif args.mode is not None:
            parser.print_help(sys.stderr)
            sys.stderr.write('\nA notification --mode may not be specified when using --delete\n')
            sys.exit(1)
        elif args.exec is not None:
            parser.print_help(sys.stderr)
            sys.stderr.write('\nThe --exec option may not be specified when using --delete\n')
            sys.exit(1)
        elif args.run is not None:
            parser.print_help(sys.stderr)
            sys.stderr.write('\nThe --run option may not be specified when using --delete\n')
            sys.exit(1)

    if args.email_credentials:
        try:
            email_creds = prompt_and_save_email_credentials()
        except KeyboardInterrupt:
            sys.exit(0)
    elif args.mode == 'email':
        email_creds = get_email_credentials()

    if args.delete:
        for notifier in notify.get_notifiers():
            if (args.PID and notifier.pid == args.PID) or (args.name is not None and notifier.name == args.name):
                pid = notifier.pid
                daemonpid = notifier.daemon_pid
                notifier.terminate()
                print(f"Deleted NWD daemon PID {daemonpid} monitoring PID {pid}")

    if args.list:
        titles = ('PID', 'Name', 'Started', 'Ended', 'Status')
        data = tuple(
            (str(n.pid), n.name, time.ctime(n.start_time), time.ctime(n.end_time), n.status.name)
            for n in notify.get_notifiers()
        )
        if not data:
            sys.stderr.write('There are no processes monitored\n')
        else:
            draw_table(titles, data)

    if args.cleanup:
        for notifier, status in notify.cleanup():
            print(f"Cleaned up monitor {notifier.daemon_pid} for process {notifier.pid} ({status.name})")

    if args.delete:
        return
    elif args.mode is None and not args.exec and not args.PID and args.name is None and args.run is None:
        return

    stdout_w = None
    stderr_w = None
    if args.run is not None:
        Notifier = partial(RunNotifier, args.run)
    elif args.mode is None or args.mode == 'desktop':
        Notifier = DesktopNotifier
    elif args.mode == 'email':
        if args.exec:
            stdout_w = tempfile.NamedTemporaryFile(prefix='stdout', suffix='.txt', delete=False)
            stderr_w = tempfile.NamedTemporaryFile(prefix='stderr', suffix='.txt', delete=False)
        Notifier = partial(EmailNotifier, *email_creds, stdout=stdout_w, stderr=stderr_w)
    elif args.mode == 'term':
        Notifier = TerminalNotifier

    if args.exec:
        pid = spawn_daemon()
        if pid > 0:
            # parent process
            args.PID = pid
        else:
            # child process
            p = subprocess.Popen(shlex.split(args.exec), stdout=stdout_w, stderr=stderr_w)
            sys.exit(p.wait())
    elif args.name is not None:
        matches = tuple(proc for proc in psutil.process_iter() if proc.name() == args.name and proc.pid != os.getpid())
        if not matches:
            sys.stderr.write(f"Error: Could not find a process named \"{args.name}\"\n")
            sys.exit(2)
        elif len(matches) > 1:
            sys.stderr.write(f"There are multiple processes running named \"{args.name}\":\n\n")
            titles = (' PID ', ' Command Line ')
            data = tuple((f" {match.pid} ", ' ' + ' '.join(match.cmdline()) + ' ') for match in matches)
            draw_table(titles, data)
            sys.stderr.write('\nPlease specify the one you want by its PID\n\n')
            sys.exit(3)
        args.PID = matches[0].pid

    try:
        monitor_pid = Notifier(args.PID).start(block=args.block)
    except Exception as e:
        sys.stderr.write(f"Error monitoring PID {args.PID}: {e}\n")
        if args.exec:
            sys.stderr.write('The execute command may have completed before we could attach an NWD monitor.\n')
        sys.exit(1)

    sys.stderr.write(f"Started monitoring daemon for PID {args.PID} at PID {monitor_pid}\n")


if __name__ == '__main__':
    main()
