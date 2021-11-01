import django_tables2 as tables
from .models import Applicant


class ApplicantTable(tables.Table):
    name = tables.Column()

    class Meta:
        model = Applicant
        template_name = "django_tables2/bootstrap.html"

    # def render_pocket_value(self, value):
    #     if value.is_integer():
    #         return '{:0.0f}'.format(value)
    #     else:
    #         return '{:0.2f}'.format(value)