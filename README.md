# Notify When Done

Notify When Done (NWD) is a utility for triggering alerts when a process finishes. Kicking off a long-running compile? NWD can post a popup notification when it's done. Starting a job on a remote server? NWD can send you an e-mail when it's done. Want to run a custom script once another finishes? NWD can facilitate that, too.

## Examples

Post a desktop notification (the default behavior) when the process with PID 1337 finishes:
```
$ nwd 1337
```

Send an e-mail when `cmake` finishes:
```
$ nwd --name cmake --mode email
```
You will be prompted to enter SMTP credentials as well as the recipient's e-mail address. This can optionally be stored in the system keychain, and can be set in advance by running `nwd --email-credentials`.

List all notifications, and cancel an existing notification:
```
$ nwd --list
PID  |Name     |Started                 |Ended                   |Status
-----+---------+------------------------+------------------------+----------
55318|python3.7|Mon Dec  3 10:31:22 2018|Mon Dec  3 10:31:22 2018|FAILED
56020|clang    |Thu Nov 29 09:58:21 2018|Thu Nov 29 09:58:22 2018|NOTIFIED
34969|Python   |Mon Dec  3 10:32:05 2018|Mon Dec  3 10:32:05 2018|MONITORING
$ nwd --delete 34969
Deleted NWD daemon PID 34972 monitoring PID 34969
```

Run a command to monitor directly from NWD:
```
$ nwd --exec 'make -j4'
```

Execute a command when a process finishes:
```
$ nwd 1337 --run 'echo Process 1337 finished!'
```

## Requirements

* Python 3.6 or newer
* [keyring](https://github.com/jaraco/keyring)
* [psutil](https://github.com/giampaolo/psutil)
* [PyObjC](https://bitbucket.org/ronaldoussoren/pyobjc) on OS X
* [PyGObject](https://pygobject.readthedocs.io/en/latest/index.html) with [GIO](https://developer.gnome.org/gio/stable/) on Linux (optional; only required if using desktop notifications)
* [win10toast](https://github.com/jithurjacob/Windows-10-Toast-Notifications) on Windows (experimental)

## License

NWD is licensed and distributed under the [AGPLv3](LICENSE) license. [Contact us](https://www.sultanik.com/) if you’re looking for an exception to the terms.
