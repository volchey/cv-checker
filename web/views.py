from .models import Applicant
from .tables import ApplicantTable
from django_tables2 import SingleTableView


class MainView(SingleTableView):
    model = Applicant
    template_name = 'tables.html'
    table_class = ApplicantTable

    def get_table_data(self):
        data = Applicant.objects.exclude()
        return data