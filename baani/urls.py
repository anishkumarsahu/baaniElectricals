"""baani URL Configuration

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/4.1/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
import re
from urllib.parse import urlsplit

from django.conf import settings
from django.contrib import admin
from django.urls import path, re_path, include
from django.http import JsonResponse
from django.conf.urls.static import static
from pwa import views as pwa_views

from baani.media import uploaded_media

def healthz(request):
    return JsonResponse({"status": "ok"})


urlpatterns = [
    path('healthz', healthz, name='healthz'),
    path('', include(('home.urls', 'home'), namespace='homeApp')),
    path('admin/', admin.site.urls),
    path('activate/', include(('activation.urls', 'activation'), namespace='activationApp')),
    path('serviceworker.js', pwa_views.service_worker, name='serviceworker'),
    path('manifest.json', pwa_views.manifest, name='manifest'),
]


media_url = urlsplit(settings.MEDIA_URL)
media_prefix = media_url.path.strip('/')
if media_prefix and not media_url.scheme and not media_url.netloc:
    urlpatterns.insert(0, re_path(r'^' + re.escape(media_prefix) + r'/(?P<path>.*)$',
                                  uploaded_media, name='uploaded_media'))

if settings.DEBUG:
    urlpatterns = urlpatterns + static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)
