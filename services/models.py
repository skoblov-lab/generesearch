from django.db import models
from django.conf import settings
import os

# Create your models here.
ERROR = 'error'
READY = 'ready'
PROCESSING = 'processing'

SUBMISSION_STATUS = (
    (PROCESSING, PROCESSING),
    (READY, READY),
    (ERROR, ERROR)
)
STATUS_VIEW_MAPPING = {
    ERROR: 'danger',
    PROCESSING: 'warning',
    READY: 'success'
}


class Submission(models.Model):
    # task identifier
    name = models.CharField('name', primary_key=True, max_length=256)
    date = models.DateTimeField('date', auto_now_add=True)
    status = models.CharField('status', choices=SUBMISSION_STATUS,
                              default=PROCESSING,
                              max_length=16, blank=True)
    message = models.TextField('message', null=True,
                               default='Processing the submission',
                               blank=True, help_text='pass a comment')
    response = models.FilePathField('response', null=True, blank=True,
                                     help_text='submission response')
    service = models.CharField(max_length=100)

    class Meta:
        ordering = ['-date']

    def isready(self) -> bool:
        return self.status == READY

    def table_view_status(self) -> str:
        """
        Status for table view
        :return:
        """
        return STATUS_VIEW_MAPPING[self.status]

    def response_url(self) -> str:
        path = os.path.relpath(self.response, settings.MEDIA_ROOT) if self.response else ''
        return os.path.join(settings.MEDIA_URL, path)


if __name__ == '__main__':
    raise RuntimeError
