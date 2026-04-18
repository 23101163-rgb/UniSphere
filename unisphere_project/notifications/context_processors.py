from .models import Notification


def create_notification(recipient, title, message, link=''):
    Notification.objects.create(
        recipient=recipient,
        title=title,
        message=message,
        link=link
    )


def unread_notifications(request):
    if request.user.is_authenticated:
        unread_count = Notification.objects.filter(
            recipient=request.user,
            is_read=False
        ).count()
        return {'unread_count': unread_count}
    return {'unread_count': 0}
