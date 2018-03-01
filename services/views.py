import os
import tempfile
from typing import Union

from celery import result
from django.conf import settings
from django.http import HttpResponseRedirect
from django.shortcuts import render
from django.urls import reverse
from multipledispatch import dispatch

from services.forms import AlleleForm, BulkForm
from services.models import Submission
from services import tasks

SUBMISSIONS = 'submissions'

BULK = 'bulk-form'
VCF_TEMPLATE = """##fileformat=VCFv4.1
#CHROM\tPOS\tID\tREF\tALT\tQUAL\tFILTER\tINFO\tFORMAT
{}\t{}\t.\t{}\t{}\t.\t.\t.\t."""


@dispatch(BulkForm)
def bmsubmit(form: BulkForm) -> str:
    """
    Submit a bulk BadMut query
    :param form: a bound form
    :return:
    """
    upload = form.cleaned_data['file']
    assembly = form.cleaned_data['assembly']
    filepath = os.path.join(settings.MEDIA_ROOT, upload.name)
    return tasks.vcfservice.delay(
        tasks.BADMUT, assembly, filepath, upload.error).task_id


@dispatch(AlleleForm)
def bmsubmit(form: AlleleForm) -> str:
    """
    Submit a point BadMut query
    :param form: a bound form
    :return:
    """
    data = form.cleaned_data
    assembly, chrom, pos, ref, alt = [
        data[key] for key in ('assembly', 'chrom', 'pos', 'ref', 'alt')
    ]
    with tempfile.NamedTemporaryFile(mode='w', dir=settings.MEDIA_ROOT,
                                     delete=False, suffix='.upload.vcf') as out:
        print(VCF_TEMPLATE.format(chrom, pos, ref, alt), file=out)
        filepath = out.name
    return tasks.vcfservice.delay(
        tasks.BADMUT, assembly, filepath, None).task_id


@dispatch(BulkForm)
def mirnasubmit(form: BulkForm) -> str:
    """
    Submit a bulk miRNA query
    :param form: a bound form
    :return:
    """
    upload = form.cleaned_data['file']
    assembly = form.cleaned_data['assembly']
    filepath = os.path.join(settings.MEDIA_ROOT, upload.name)
    return tasks.vcfservice.delay(
        tasks.MIRNA, assembly, filepath, upload.error).task_id


def bind(request) -> Union[BulkForm, AlleleForm]:
    """
    Bind a request to a form
    :param request:
    :return:
    """
    form = (BulkForm if any(key.startswith(BULK) for key in request.POST) else
            AlleleForm)
    return form(request.POST, request.FILES)


def badmut_service(request):
    if request.method == 'POST':
        form = bind(request)
        if form.is_valid():
            # bind task ID to user's submissions
            request.session.setdefault(SUBMISSIONS, []).append(bmsubmit(form))
            request.session.modified = True
            return HttpResponseRedirect(reverse('submissions'))
    return render(request, 'badmut.html',
                  {'allele_form': AlleleForm(), 'bulk_form': BulkForm()})


def mirna_service(request):
    if request.method == 'POST':
        form = bind(request)
        if form.is_valid():
            # bind task ID to user's submissions
            request.session.setdefault(SUBMISSIONS, []).append(mirnasubmit(form))
            request.session.modified = True
            return HttpResponseRedirect(reverse('submissions'))
    return render(request, 'mirna.html', {'bulk_form': BulkForm()})


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
