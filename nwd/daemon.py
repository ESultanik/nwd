import os
import sys


def spawn_daemon():
    # do the UNIX double-fork magic, see Stevens' "Advanced
    # Programming in the UNIX Environment" for details (ISBN 0201563177)
    try:
        r, w = os.pipe()
        pid = os.fork()
        if pid > 0:
            # we are the parent process
            return int(os.fdopen(r).readline().strip())
    except OSError as e:
        sys.stderr.write(f"fork #1 failed: {e.errno} ({e.strerror})\n")
        sys.exit(os.EX_OSERR)

    os.setsid()

    # do second fork
    try:
        pid = os.fork()
        if pid > 0:
            # we are the parent process; let our parent know about our child's PID:
            os.write(w, f"{pid}\n".encode('utf8'))
            sys.exit(os.EX_OK)
    except OSError as e:
        sys.stderr.write(f"fork #2 failed: {e.errno} ({e.strerror})")
        sys.exit(os.EX_OSERR)
    return 0
