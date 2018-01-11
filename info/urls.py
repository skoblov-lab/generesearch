from django.conf.urls import url
from django.views.generic import TemplateView

from . import views


urlpatterns = [
    url(r'^$', views.EventListView.as_view(template_name='home.html'),
        name='home'),
    url(r'^home/$', views.EventListView.as_view(template_name='home.html'),
        name='home'),
    url(r'^events/$', views.EventListView.as_view(template_name='events.html'),
        name='events'),
    url(r'^team/$', views.EmployeeListView.as_view(),
        name='team'),
    url(r'^event/(?P<pk>\d+)$', views.EventDetailView.as_view(),
        name='event-detail'),
    url(r'^about/$', TemplateView.as_view(template_name='about.html'),
        name='about'),
    url(r'^join/$', TemplateView.as_view(template_name='join.html'),
        name='join'),
    url(r'^publications/$', views.PublicationListView.as_view(),
        name='publications')
]
