from django.contrib import admin
from .models import Vacancy, Candidate, Resume, Requirements, Skills, Required_skills

admin.site.register(Vacancy)
admin.site.register(Candidate)
admin.site.register(Resume)
admin.site.register(Requirements)
admin.site.register(Skills)
admin.site.register(Required_skills)