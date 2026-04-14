from user.models import Message, Report


def get_notification_count(user, **kwargs):
    num_notifications = 0

    # Count the number of unread messages for the user
    num_notifications += Message.objects.filter(
        recipient=user,
        read_receipt=False
    ).count()

    num_notifications += Report.objects.filter(
        pressure_map_reading__reading_equipment__user=user,
        pressure_alert=True,
        read_receipt=False
    ).count()
    # Space for future notification types (e.g., reminders)

    # num_notifications += other_notification_counts...

    return num_notifications


def get_notifications(user, **kwargs):
    # Get unread messages for the user
    unread_messages = Message.objects.filter(
        recipient=user,
        read_receipt=False
    ).order_by('-timestamp')

    unviewed_pressure_alerts = Report.objects.filter(
        pressure_map_reading__reading_equipment__user=user,
        pressure_alert=True,
        read_receipt=False
    ).order_by('-created_at')

    unviewed_reports = Report.objects.filter(
        pressure_map_reading__reading_equipment__user=user,
        read_receipt=False
    ).order_by('-created_at')


    # Space for future notification types (e.g., pressure alerts, reminders)

    notifications = {
        'messages': unread_messages,
        'pressure_alerts': unviewed_pressure_alerts,
        'reports': unviewed_reports,
        # 'reminders': reminders,
    }

    return notifications
