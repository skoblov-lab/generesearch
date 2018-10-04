from django.conf.urls import url

from services import actions
from services import views

badmut_view = views.make_annotation_service_view(
    actions.badmut,
    'badmut.html',
    views.make_blank_badmut_forms()
)

mirna_view = views.make_annotation_service_view(
    actions.mirna,
    'mirna.html',
    views.make_blank_mirna_forms()
)

urlpatterns = [
    url(r'^badmut/$', badmut_view, name='badmut'),
    url(r'^mirna/$', mirna_view, name='mirna'),
    url(r'^submissions/$', views.submissions, name='submissions'),
]
