from django.db import models
from django.utils import timezone

# Create your models here.
class Vacancy(models.Model):
    class Meta:
        verbose_name_plural = "vacancies"

    id = models.AutoField(primary_key=True)
    name = models.CharField(max_length=255)
    description = models.TextField()

    class Status(models.IntegerChoices):
        Open = 1
        Closed = 2

    status = models.IntegerField(
        choices=Status.choices,
        default=Status.Open,
    )

    timestamp = models.DateTimeField(default=timezone.now)

    def __str__(self):
        return self.name