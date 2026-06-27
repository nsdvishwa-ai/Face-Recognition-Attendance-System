import face_recognition
import json

from django.db.models.signals import post_save
from django.dispatch import receiver

from .models import Employee


@receiver(post_save, sender=Employee)
def generate_face_encoding(sender, instance, created, **kwargs):

    if instance.image:

        image = face_recognition.load_image_file(instance.image.path)

        encodings = face_recognition.face_encodings(image)

        if len(encodings) > 0:

            instance.face_encoding = json.dumps(
                encodings[0].tolist()
            )

            Employee.objects.filter(
                id=instance.id
            ).update(
                face_encoding=instance.face_encoding
            )