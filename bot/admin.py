from django.contrib import admin
from .models import Vacancy, Candidate, Resume

admin.site.register(Vacancy)
admin.site.register(Candidate)
admin.site.register(Resume)