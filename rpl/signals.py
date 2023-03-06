from django.dispatch import receiver
from django.db.models.signals import post_save
from .models import Device


@receiver(post_save, sender=Device)
def add_sensor(sender, instance, created, **kwarg):
    if created:
        match instance.fun:
            case 'rfid':
                instance.rfid.create()
            case 'btn':
                instance.button.create()