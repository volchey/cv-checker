from .models import Applicant
from bot.models import Vacancy, Candidate, Resume
from .tables import CandidateTable
from django.views.generic.base import TemplateView, View
from web.forms import Registration
from django.contrib.auth.models import User, AnonymousUser
from django.contrib.auth import authenticate
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib.auth.forms import UserCreationForm
from django.views.generic.edit import FormView
from django.core.exceptions import ValidationError
from django.views.generic import CreateView
from django.http import HttpResponse


class MainView(LoginRequiredMixin, TemplateView):
    template_name = 'tables.html'

    def parse_file(self, resumes):
        info = []
        for resume in resumes:
            list_resume = resume.extracted_text.split('\n')
            if ('Email' or 'email') in list_resume:
                position = list_resume.index('Email')
                info.append({resume.id : list_resume[(position+1):(position+2)]})
        return info

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        vacancy_id = self.request.GET.get('vacancy_id')
        resumes = Resume.objects.all().select_related('candidate', 'vacancy')
        if vacancy_id:
            resumes = resumes.filter(vacancy__id=vacancy_id)
        context['resumes'] = resumes
        file_content = self.parse_file(resumes)
        context['email'] = file_content
        context['resumes'] = resumes
        context['vacancy_open'] = Vacancy.objects.filter(status=Vacancy.Status.Open)
        return context

    def form_valid(self, form):
        print('form_valid called')
        object = form.save(commit=False)
        print(self.request.user)
        if self.request.user.is_authenticated:
            object.owner = self.request.user
        object.save()
        return super(CreateView, self).form_valid(form)


class RegistrationView(FormView):
    template_name = 'registration/registration.html'
    form_class = Registration
    success_url = 'all'

    def form_valid(self, form):
        # This method is called when valid form data has been POSTed.
        # It should return an HttpResponse.
        password = form.clean_password2()
        name = form.clean_name()
        user = authenticate(self.request, username=name, password=password)
        if user is None:
            us1 = User.objects.create_user(name, None, password)
            us1.save()
        else:
            print("User already exits!")
            raise ValidationError("User already exits!")
        return super().form_valid(form)

class HomePageView(TemplateView):
    template_name = 'main.html'

    
    
