import datetime
import os
from contextlib import suppress

import pytz
from celery import shared_task
from celery.result import AsyncResult
from celery.schedules import crontab
from celery.task import periodic_task
from django.conf import settings

from services import actions
from services.models import ERROR, READY, Submission

OUTPUT = 'output'
BADMUT = 'badmut'
MIRNA = 'mirna'
VCFSERVICES = {
    BADMUT: 'BadMut',
    MIRNA: 'miRNA'
}


@shared_task
def annotation_service(action_name: str, *args, **kwargs):
    action = actions.ACTIONS[action_name]
    submission = Submission(annotation_service.request.id, service=action_name)
    submission.save()
    result = action(*args, **kwargs)
    submission.status = READY if result else ERROR
    submission.response = result.value if result else None
    submission.message = 'Done!' if result else str(result.exception)
    submission.save()


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
