from django.db import models

class SingletonModel(models.Model):
    """Singleton Django Model"""

    class Meta:
        abstract = True

    def save(self, *args, **kwargs):
        self.pk = 1
        return super().save(*args, **kwargs)

    @classmethod
    def singleton(cls):
        obj, _ = cls.objects.get_or_create(pk=1)
        return obj