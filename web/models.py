from django.db import models


# Create your models here.


class Applicant(models.Model):
    name = models.CharField(max_length=20)
    surname = models.CharField(max_length=20)
    vacancy = models.CharField(max_length=30)
    arrival_date = models.DateTimeField('arrival date', null=True, blank=True)
    cv = models.CharField(max_length=20)


    def __str__(self):
        return self.name