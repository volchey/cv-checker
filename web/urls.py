from django.urls import path
from . import views
from web import views
from django.conf import settings
from django.conf.urls.static import static

app_name = 'web'
urlpatterns = [
    # path('', views.MainView.as_view()),
    path('', views.HomePageView.as_view(), name='home'),
    path('all', views.MainView.as_view(), name='all'),
    path('registration', views.RegistrationView.as_view(), name='registration')
] + static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)