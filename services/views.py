from typing import Optional

from django.http import HttpResponseRedirect, HttpRequest
from django.shortcuts import render
from django.urls import reverse

from services.forms import BaseAnnotationServiceForm, PointAnnotationForm, \
    AlleleAnnotationForm, VcfAnnotationForm, TSV
from services.models import Submission

SUBMISSIONS = 'submissions'
FORM_SERVICE_TAG = 'service'
POINT_FORM = 'point_form'
ALLELE_FORM = 'allele_form'
VCF_FORM = 'vcf_form'
SERVICE_FORM_MAP = {
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
    form = SERVICE_FORM_MAP.get(service_tag)
    return None if form is None else form(request.POST, request.FILES)


def make_annotation_service_view(submitter, template, blank_forms):

    def view(request):
        if request.method == 'POST':
            form = bind_service_form(request)
            if form is not None and form.is_valid():
                # bind task ID to user's submissions
                submission = submitter(form)
                request.session.setdefault(SUBMISSIONS, []).append(submission)
                request.session.modified = True
                return HttpResponseRedirect(reverse('submissions'))
        return render(request, template, blank_forms())

    return view


def make_blank_badmut_forms():
    allele_form = AlleleAnnotationForm(
        initial={'compress': False, 'output_format': TSV}
    )
    vcf_form = VcfAnnotationForm()
    return {ALLELE_FORM: allele_form, VCF_FORM: vcf_form}


def make_blank_mirna_forms():
    point_form = PointAnnotationForm(
        initial={'compress': False, 'output_format': TSV}
    )
    vcf_form = VcfAnnotationForm()
    return {POINT_FORM: point_form, VCF_FORM: vcf_form}


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
