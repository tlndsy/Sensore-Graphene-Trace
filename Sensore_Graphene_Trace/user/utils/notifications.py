from user.models import Message


def get_notification_count(user, **kwargs):
    num_notifications = 0

    # Count the number of unread messages for the user
    num_notifications += Message.objects.filter(
        recipient=user,
        read_receipt=False
    ).count()

    # Space for future notification types (e.g., pressure alerts, reminders)

    # num_notifications += other_notification_counts...

    return num_notifications

def get_notifications(user, **kwargs):

    # Get unread messages for the user
    unread_messages = Message.objects.filter(
        recipient=user,
        read_receipt=False
    ).order_by('-timestamp')

    # Space for future notification types (e.g., pressure alerts, reminders)

    notifications = {
        'messages': unread_messages,
        # 'pressure_alerts': pressure_alerts,
        # 'reminders': reminders,
    }

    return notifications