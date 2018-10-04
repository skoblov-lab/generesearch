from typing import Optional, Callable

from django.http import HttpResponseRedirect, HttpRequest
from django.shortcuts import render
from django.urls import reverse

from services.forms import BaseAnnotationServiceForm, PointAnnotationForm, \
    AlleleAnnotationForm, VcfAnnotationForm
from services.models import Submission
from services import tasks

SUBMISSIONS = 'submissions'
FORM_SERVICE_TAG = 'service'
POINT_FORM = 'point_form'
ALLELE_FORM = 'allele_form'
VCF_FORM = 'vcf_form'
ANNOTATION_SERVICE_FORM_MAP = {
    POINT_FORM: PointAnnotationForm,
    ALLELE_FORM: AlleleAnnotationForm,
    VCF_FORM: VcfAnnotationForm
}


def bind_service_form(request: HttpRequest) \
        -> Optional[BaseAnnotationServiceForm]:
    """
    Bind a request to a form
    :param request:
    :return:
    """
    service_tag = str(request.POST.get(FORM_SERVICE_TAG))
    form = ANNOTATION_SERVICE_FORM_MAP.get(service_tag)
    return None if form is None else form(request.POST, request.FILES)


def make_annotation_service_view(action: tasks.ServiceAction, template: str,
                                 blank_forms: Callable):

    def view(request):
        if request.method == 'POST':
            form = bind_service_form(request)
            if form is not None and form.is_valid():
                # bind task ID to user's submissions
                submission = tasks.annotation_service.delay(action, form)

                request.session.setdefault(SUBMISSIONS, []).append(submission)
                request.session.modified = True
                return HttpResponseRedirect(reverse('submissions'))
        return render(request, template, blank_forms())

    return view


def make_blank_badmut_forms():
    return {ALLELE_FORM: AlleleAnnotationForm(), VCF_FORM: VcfAnnotationForm()}


def make_blank_mirna_forms():
    # point_form = PointAnnotationForm(
    #     initial={'compress': False, 'output_format': TSV})
    return {POINT_FORM: PointAnnotationForm(), VCF_FORM: VcfAnnotationForm()}


def submissions(request):
    # remove expired (cleaned up) submissions
    logged = request.session.get(SUBMISSIONS, [])
    available = list(Submission.objects.all().filter(name__in=logged))
    # request.session[SUBMISSIONS] = [sub.name for sub in available]
    # request.session.modified = True
    return render(request, 'submissions.html',
                  context=dict(submissions=available))


if __name__ == '__main__':
    raise RuntimeError
