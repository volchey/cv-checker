from django.db import models
from django.db.models.expressions import Value
import django_tables2 as tables
from bot.models import Candidate, Resume, Vacancy


class CandidateTable(tables.Table):
    # vacancy = tables.Column(Resume.vacancy)
    # file = tables.Column()

    class Meta:
        model = Candidate
        template_name = "django_tables2/bootstrap.html"

    # def render_pocket_value(self, value):
    #     if value.is_integer():
    #         return '{:0.0f}'.format(value)
    #     else:
    #         return '{:0.2f}'.format(value)