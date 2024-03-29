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
    email = models.CharField(max_length=64, default='')

    def __str__(self) -> str:
        return self.name + ' ' + self.surname

class Resume(models.Model):
    id = models.AutoField(primary_key=True)
    candidate = models.ForeignKey(Candidate, on_delete=models.CASCADE)
    vacancy = models.ForeignKey(Vacancy, on_delete=models.CASCADE)
    file = models.FileField(upload_to='files/')
    cover_letter = models.TextField(default='')
    extracted_text = models.TextField(default='')

    def __str__(self) -> str:
        return f'Resume from {self.candidate}'

class Requirements(models.Model):
    id = models.AutoField(primary_key=True)
    candidate = models.ForeignKey(Candidate, on_delete=models.CASCADE)
    name = models.CharField(max_length=64,default='')
    value = models.TextField(max_length=64,default='')

    def __str__(self) -> str:
        return f'{self.name} {self.candidate}'

class Required_skills(models.Model):
    id = models.AutoField(primary_key=True)
    vacancy = models.ForeignKey(Vacancy, on_delete=models.CASCADE)
    value = models.TextField(max_length=64,default='')

    def __str__(self) -> str:
        return f'{self.value} for {self.vacancy}'

class Skills(models.Model):
    id = models.AutoField(primary_key=True)
    candidate = models.ForeignKey(Candidate, on_delete=models.CASCADE)
    skill = models.ForeignKey(Required_skills, on_delete=models.CASCADE)
    exist = models.BooleanField(default=False)

    def __str__(self) -> str:
        return f'{self.skill} for {self.candidate}'