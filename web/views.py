from .models import Applicant
from bot.models import Vacancy, Candidate, Resume
from .tables import CandidateTable
from django_tables2 import SingleTableView
from django.views.generic.base import TemplateView


class MainView(TemplateView):
    template_name = 'tables.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        vacancy_id = self.request.GET.get('vacancy_id')
        resumes = Resume.objects.all().select_related('candidate', 'vacancy')
        if vacancy_id:
            resumes = resumes.filter(vacancy__id=vacancy_id)
        context['resumes'] = resumes
        context['vacancy_open'] = Vacancy.objects.filter(status=Vacancy.Status.Open)
        return context