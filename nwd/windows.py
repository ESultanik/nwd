from win10toast import ToastNotifier


def notify(title, subtitle, info_text, duration=5):
    ToastNotifier().show_toast(f"{title}: {subtitle}",
                               info_text,
                               icon_path=None,
                               duration=duration)
