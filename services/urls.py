from django.conf import settings
from django.conf.urls import url, include
from django.views.generic import TemplateView
from django.views.static import serve

from . import views

urlpatterns = [
    url(r'^badmut/$', views.badmut_service, name='badmut'),
    url(r'^mirna/$', TemplateView.as_view(template_name='mirna.html'),
        name='mirna'),
    url(r'^submissions/$', views.submissions, name='submissions'),
]
