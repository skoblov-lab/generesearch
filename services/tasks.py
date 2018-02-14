from contextlib import suppress
import datetime
import os
import subprocess as sp
from typing import Optional

import pytz
from celery import shared_task
from celery.schedules import crontab
from celery.task import periodic_task
from celery.result import AsyncResult
from django.conf import settings

from services.models import ERROR, READY, Submission

OUTPUT = 'output'
BADMUT = 'badmut'
MIRNA = 'mirna'
VCFQUERY_SERVICES = {
    BADMUT: 'BadMut',
    MIRNA: 'miRNA'
}


class RequestInputType:
    snv = 1
    bulk = 2


class InputValidationError(ValueError):
    pass


@shared_task
def vcfquery(service: str, assembly: str, input_file: str, error: Optional[str]):
    if service not in VCFQUERY_SERVICES:
        raise ValueError(
            f'service must be one if {list(VCFQUERY_SERVICES.keys())}')
    submission = Submission(vcfquery.request.id,
                            service=VCFQUERY_SERVICES[service])
    submission.save()
    output_file = f'{input_file.split(".", 1)[0]}.{service}.vcf.gz'
    service = os.path.join(settings.SERVICES_ROOT, service, service + '.sh')
    command = [service, assembly, input_file, output_file]
    try:
        if error is not None:
            submission.status = ERROR
            submission.message = error
            raise ValueError
        sp.run(command, check=True, stderr=sp.PIPE)
        submission.status = READY
        submission.response = output_file
        submission.message = 'Done!'
    except (sp.CalledProcessError, ValueError):
        submission.status = ERROR
        submission.message = 'Invalid file format'
    finally:
        submission.save()
        with suppress(FileNotFoundError, TypeError):
            os.remove(input_file)


# @periodic_task(run_every=crontab(minute=0, hour='*/1'))
@periodic_task(run_every=crontab(minute='*/30', hour='*/1'))
def cleanup_submissions():
    """
    Remove expired submissions every 30 minutes
    :return:
    """
    now = datetime.datetime.now(pytz.timezone(settings.TIME_ZONE))

    def hasexpired(sub: Submission) -> bool:
        seconds = (now - sub.date).total_seconds()
        return seconds > settings.SUBMISSION_LIFESPAN_SECONDS

    expired = list(filter(hasexpired, Submission.objects.all()))
    tasks = [AsyncResult(submission.name) for submission in expired]
    for submission, task in zip(expired, tasks):
        # delete result if result is a file
        with suppress(FileNotFoundError, TypeError):
            os.remove(submission.response)
        submission.delete()
        task.forget()


if __name__ == '__main__':
    raise RuntimeError
