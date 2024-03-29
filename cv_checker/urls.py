from django.conf import settings
from django.conf.urls import include
from django.contrib import admin
from django.urls import path

# Remove this when you start your proejct
from django.views import debug
from django.conf import settings
from django.conf.urls.static import static

urlpatterns = [
    path('admin/', admin.site.urls),
    # path('', debug.default_urlconf),
    path('', include('web.urls')),
    path('accounts/', include('django.contrib.auth.urls'))
] + static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)


if settings.DEBUG:
    import debug_toolbar

    urlpatterns += [
        path('__debug__/', include(debug_toolbar.urls)),
    ]
