try:
    import gi
except ModuleNotFoundError:
    raise ModuleNotFoundError("PyGObject is required to generate desktop notifications on your system. "
                              "Please install it using the instructions "
                              "here: https://pygobject.readthedocs.io/en/latest/getting_started.html")

gi.require_version('Gio', '2.0')


def notify(title, subtitle, info_text):
    from gi.repository import Gio

    NWD = Gio.Application.new("NWD", Gio.ApplicationFlags.FLAGS_NONE)
    NWD.register()

    notification = Gio.Notification.new(subtitle)
    notification.set_body(info_text)
    icon = Gio.ThemedIcon.new("dialog-information")
    notification.set_icon(icon)
    NWD.send_notification(None, notification)
