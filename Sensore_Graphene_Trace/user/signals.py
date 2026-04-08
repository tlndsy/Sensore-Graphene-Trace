from django.db.models.signals import post_save
from django.contrib.auth.models import Group
from django.dispatch import receiver

from .models import User, Message, Conversation

@receiver(post_save, sender=User)
def assign_group(sender, instance, created, **kwargs):
    if created:
        group, _ = Group.objects.get_or_create(name=instance.role)
        instance.groups.add(group)

@receiver(post_save, sender=Message)
def update_last_message(sender, instance, created, **kwargs):
    if created:
        Conversation.objects.filter(pk=instance.conversation_id).update(
            last_message=instance,
            updated_at=instance.timestamp
        )