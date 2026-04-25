from .models import Notification


def create_notification(recipient=None, user=None, title='', message='', link=''):
    target_user = recipient or user

    if not target_user:
        raise ValueError("create_notification() requires either 'recipient' or 'user'.")

    return Notification.objects.create(
        recipient=target_user,
        title=title,
        message=message,
        link=link or ''
    )