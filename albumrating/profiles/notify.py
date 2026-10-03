from .models import Notification

def notify(recipient, actor, kind, **about):
    # about: review=..., artist_review=..., comment=... (whatever the notification is about).
    # Nobody gets notified about their own actions.
    if recipient != actor:
        Notification.objects.create(recipient=recipient, actor=actor, kind=kind, **about)

def unnotify(recipient, actor, kind, **about):
    # Undo a notification, e.g. when someone unlikes or unfollows.
    Notification.objects.filter(recipient=recipient, actor=actor, kind=kind, **about).delete()
