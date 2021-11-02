from django.db import models
from django.utils import timezone

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

class Candidate(models.Model):
    id = models.AutoField(primary_key=True)
    name = models.CharField(max_length=32)
    surname = models.CharField(max_length=32)

class Resume(models.Model):
    id = models.AutoField(primary_key=True)
    candidate = models.ForeignKey(Candidate, on_delete=models.CASCADE)
    vacancy = models.ForeignKey(Vacancy, on_delete=models.CASCADE)
    file = models.FileField(upload_to='files/')
    cover_letter = models.TextField(default='')