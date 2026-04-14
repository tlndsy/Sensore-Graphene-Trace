from django.utils import timezone
from user.models import Message, Report

from collections import OrderedDict


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
    unread_messages = Message.objects.filter(
        recipient=user,
        read_receipt=False
    )

    unviewed_pressure_alerts = Report.objects.filter(
        pressure_map_reading__reading_equipment__user=user,
        pressure_alert=True,
        read_receipt=False
    )

    unviewed_reports = Report.objects.filter(
        pressure_map_reading__reading_equipment__user=user,
        read_receipt=False
    )

    notifications = []

    # Messages
    for msg in unread_messages:
        notifications.append({
            "type": "message",
            "object": msg,
            "text": f"💬 Unread Message From {msg.sender.first_name}: {msg.content[:50]}",
            "timestamp": msg.timestamp,
        })

    # Pressure alerts
    for alert in unviewed_pressure_alerts:
        notifications.append({
            "type": "pressure_alert",
            "object": alert,
            "text": f"⚠️ Pressure alert: {alert.pressure_map_reading.reading_equipment.custom_name}",
            "timestamp": alert.pressure_map_reading.timestamp,
        })

    # Reports
    for report in unviewed_reports:
        notifications.append({
            "type": "report",
            "object": report,
            "text": "📄 Unread report from: " + report.pressure_map_reading.reading_equipment.custom_name,
            "timestamp": report.pressure_map_reading.timestamp,
        })

    # Sort into single timeline
    notifications.sort(key=lambda x: x["timestamp"], reverse=True)

    # Group notifications by date
    today = timezone.now().date()
    yesterday = today - timezone.timedelta(days=1)

    grouped = OrderedDict()

    for n in notifications:
        date = n["timestamp"].date()

        if date == today:
            key = "Today"
        elif date == yesterday:
            key = "Yesterday"
        else:
            key = date.strftime("%d %b %Y")

        grouped.setdefault(key, []).append(n)

    return grouped

