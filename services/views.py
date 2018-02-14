import os
import tempfile
from typing import Union

from django.conf import settings
from django.http import HttpResponseRedirect
from django.shortcuts import render
from django.urls import reverse
from multipledispatch import dispatch

from services import tasks
from services.forms import AlleleForm, BulkForm
from services.models import Submission

SUBMISSIONS = 'submissions'

BULK = 'bulk-form'
VCF_TEMPLATE = """##fileformat=VCFv4.1
#CHROM\tPOS\tID\tREF\tALT\tQUAL\tFILTER\tINFO
{}\t{}\t.\t{}\t{}\t.\t.\t."""


@dispatch(BulkForm)
def submit_vcfquery(form: BulkForm, service: str) -> str:
    """
    Submit a bulk BadMut query
    :param form: a bound form
    :param service: service itentifier: should be one of tasks.VCFQUERY_SERVICES
    :return:
    """
    if service not in tasks.VCFQUERY_SERVICES:
        raise ValueError(
            f'service must be one if {list(tasks.VCFQUERY_SERVICES.keys())}')
    upload = form.cleaned_data['file']
    assembly = form.cleaned_data['assembly']
    filepath = os.path.join(settings.MEDIA_ROOT, upload.name)
    return tasks.vcfquery.delay(service, assembly, filepath, upload.error).task_id


@dispatch(AlleleForm)
def submit_vcfquery(form: AlleleForm, service: str) -> str:
    """
    Submit a point BadMut query
    :param form: a bound form
    :param service: service itentifier: should be one of tasks.VCFQUERY_SERVICES
    :return:
    """
    if service not in tasks.VCFQUERY_SERVICES:
        raise ValueError(
            f'service must be one if {list(tasks.VCFQUERY_SERVICES.keys())}')
    data = form.cleaned_data
    assembly, chrom, pos, ref, alt = [
        data[key] for key in ('assembly', 'chrom', 'pos', 'ref', 'alt')
    ]
    with tempfile.NamedTemporaryFile(mode='w', dir=settings.MEDIA_ROOT,
                                     delete=False, suffix='.upload.vcf') as out:
        print(VCF_TEMPLATE.format(chrom, pos, ref, alt), file=out)
        filepath = out.name
    return tasks.vcfquery.delay(service, assembly, filepath, None).task_id


def bind_vcfquery(request) -> Union[BulkForm, AlleleForm]:
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
        form = bind_vcfquery(request)
        if form.is_valid():
            # bind task ID to user's submissions
            taskid = submit_vcfquery(form, tasks.BADMUT)
            request.session.setdefault(SUBMISSIONS, []).append(taskid)
            request.session.modified = True
            return HttpResponseRedirect(reverse('submissions'))
    return render(request, 'badmut.html',
                  {'allele_form': AlleleForm(), 'bulk_form': BulkForm()})


def mirna_service(request):
    if request.method == 'POST':
        form = bind_vcfquery(request)
        if form.is_valid():
            # bind task ID to user's submissions
            taskid = submit_vcfquery(form, tasks.MIRNA)
            request.session.setdefault(SUBMISSIONS, []).append(taskid)
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
