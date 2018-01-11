import datetime
import os

from django.db import models
from django.urls import reverse
from django.conf import settings


class Event(models.Model):
    """
    Laboratory event representation
    """

    type = models.CharField('Event', max_length=50, help_text='Event type')
    title = models.CharField('Title', max_length=100)
    abstract = models.CharField('Abstract', max_length=100)
    description = models.TextField('Description', null=True, blank=True)
    link = models.URLField('Link', blank=True, null=True)
    start = models.DateField('Start', default=datetime.datetime.now)
    end = models.DateField('End', null=True, blank=True)

    class Meta:
        ordering = ['-start']

    def get_absolute_url(self):
        """
        :return: URL to a particular event.
        """
        return reverse('event-detail', args=[str(self.id)])

    def __str__(self):
        return f'{self.title}'


class Employee(models.Model):
    """
    Represents an employee.
    """
    first_name = models.CharField('First Name', max_length=100)
    last_name = models.CharField('Last Name', max_length=100)
    academic_degree = models.CharField('Degree', max_length=50, null=True,
                                       blank=False)
    position = models.CharField('Position', max_length=50)
    interests = models.TextField('Interests', null=True, blank=True,
                                 help_text='A coma-separated list of interests')
    email = models.EmailField(blank=True, null=True)
    image = models.ImageField('Photo')
    priority = models.SmallIntegerField('List priority group', default=0,
                                        help_text='Lower groups come first')

    class Meta:
        ordering = ['priority']

    def get_absolute_url(self):
        """
        :return: URL to a particular employee.
        """
        return reverse('employee-detail', args=[str(self.id)])

    def list_interests(self) -> list:
        return self.interests.split(',')

    def image_url(self) -> str:
        path = os.path.relpath(self.image.path, settings.MEDIA_ROOT)
        return os.path.join(settings.MEDIA_URL, path)

    def __str__(self):
        return f'{self.first_name} {self.last_name}, {self.academic_degree}'


class Publication(models.Model):
    """
    Represents a publication
    """
    title = models.TextField('Title')
    authors = models.TextField('Authors')
    journal = models.CharField('Journal', max_length=100)
    year = models.PositiveIntegerField('Year Published')
    link = models.URLField('Link', null=True, blank=True)

    class Meta:
        ordering = ['-year']

    def __str__(self):
        return f'{self.authors}: {self.title} ({self.year}) {self.journal}'

    def get_absolute_url(self):
        """
        :return: URL to a particular publication
        """
        return reverse('publication-details', args=[str(self.id)])


if __name__ == '__main__':
    raise RuntimeError
