from typing import Optional, Callable
import logging

from django.http import HttpResponseRedirect, HttpRequest
from django.shortcuts import render
from django.urls import reverse

from services.forms import BaseAnnotationServiceForm, PointAnnotationForm, \
    AlleleAnnotationForm, VcfAnnotationForm
from services.models import Submission
from services import tasks
from services import optional

import traceback

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


def make_annotation_service_view(action: optional.ServiceAction, template: str,
                                 blank_forms: Callable):

    def view(request):
        if request.method == 'POST':
            form = bind_service_form(request)
            with open('/home/user/test.txt', 'w') as out:
                if form is not None and form.is_valid():
                    logging.warning('form ok')
                    # bind task ID to user's submissions
                    # TODO this will fail if action does not have a proper name
                    # TODO or if it is not added to actions.ACTIONS dictionary
                    try:
                        submission = tasks.annotation_service.delay(
                            action.__name__, form.serialise_fields()
                        )
                    except Exception as err:
                        traceback.print_tb(err.__traceback__, file=out)
                        raise err
                    request.session.setdefault(SUBMISSIONS, []).append(submission.task_id)
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
