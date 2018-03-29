from collections import OrderedDict
from functools import reduce
from typing import List

from django.core.exceptions import ValidationError
from django.db import models
from fn import F

from info.models import Employee

MUTCLASSES = frozenset([
    'UNK', 'ORG', 'CEL', 'PAT', 'PRO', 'MIM', 'ENZ', 'TRA', 'CHA', 'CAR', 'LOC',
    'INT', 'IND'
])
MUTLEVELS = frozenset([
    '--', '!--', '-', '!-', '0', '+', '!+', '++', '!++', 'r', '!r', '?'
])


def israw(annotation: str) -> bool:
    return annotation.startswith('[RAW]')


def parse_mutagenesis(lines: str):
    if not lines.strip().startswith('>'):
        raise ValueError('The input does not start with a subrecord entry')

    def parse_subrecord(recs: List[List], line: str):
        if line.startswith('>'):
            return recs.append([line.lstrip('> ')]) or recs
        cls, *spec = map(str.strip, line.split('|'))
        if cls.upper().strip('[]?') not in MUTCLASSES:
            raise ValueError(f'Unsupported effect class: {cls}')
        if cls.upper() == 'UNK' and spec:
            raise ValueError(f"UNK effects can't have specs: {line}")
        if len(spec) > 3:
            raise ValueError(f'Incorrect annotation format: {line}')

        lvl, target, assoc = (
            [val if val != '?' else None for val in spec] + [None]*(3-len(spec))
        )
        if lvl and lvl not in MUTLEVELS:
            raise ValueError(f'Unsupported effect level: {lvl}')
        return recs[-1].append([cls.upper(), lvl, target, assoc]) or recs
    subrecords = OrderedDict((entry, anno) for entry, *anno in reduce(
        parse_subrecord,
        (F(str.splitlines) >> (map, str.strip) >> (filter, bool) >> list)(lines),
        []
    ))
    if not all(subrecords.values()):
        raise ValueError('Unannotated and empty subrecords are not allowed')
    return subrecords


def validate_mutagenesis(value: str):
    if not israw(value):
        try:
            parse_mutagenesis(value)
        except ValueError as err:
            raise ValidationError(str(err))


class Annotator(models.Model):
    name = models.CharField('Name', max_length=50)

    def __str__(self):
        return self.name


class MutagenesisRecord(models.Model):
    name = models.CharField('Title', max_length=200)
    description = models.TextField('Description')
    by = models.ForeignKey(Annotator, verbose_name='Annotator', null=True, blank=True)
    completed = models.BooleanField('Completed', default=False)
    subrecords = models.TextField('Subrecords', validators=[validate_mutagenesis])

    def __str__(self):
        return f'{self.name} {self.description}...'

    def clean(self):
        if self.completed and israw(self.subrecords):
            raise ValidationError('Conflicting [RAW] and Completed')


if __name__ == '__main__':
    raise RuntimeError
