from itertools import islice, takewhile, repeat
from typing import Iterator, Iterable

from django.views import generic

from .models import Event, Employee, Publication


# Create your views here.


def sliceby(n: int, iterable: Iterable) -> Iterator:
    """
    Slice an iterable into chunks of n elements
    """
    iterator = iter(iterable)
    return takewhile(bool, (list(islice(iterator, n)) for _ in repeat(None)))


class PaginatedListView(generic.ListView):
    paginate_by = 10


class EventListView(PaginatedListView):
    model = Event
    context_object_name = 'events'


class EventDetailView(generic.DetailView):
    model = Event
    template_name = 'event.html'


class PublicationListView(PaginatedListView):
    model = Publication
    template_name = 'publications.html'
    context_object_name = 'publications'


class EmployeeListView(PaginatedListView):
    model = Employee
    template_name = 'team.html'
    context_object_name = 'employees'


if __name__ == '__main__':
    raise RuntimeError
