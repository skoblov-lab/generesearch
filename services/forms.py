from django import forms
from itertools import chain


HG19 = '19'
HG38 = '38'
ASSEMBLIES = ((HG38,)*2, (HG19,)*2)
NUCLEOTIDES = (
    ('A', 'A'),
    ('C', 'C'),
    ('G', 'G'),
    ('T', 'T')
)
CHROMOSOMES = tuple(
    (chrom, chrom) for chrom in map(str, chain(range(1, 23), 'MXY'))
)


class AssemblyForm(forms.Form):
    assembly = forms.CharField(widget=forms.Select(choices=ASSEMBLIES),
                               label="Human genome assembly version",
                               max_length=2, required=True)


class PointForm(AssemblyForm):
    chrom = forms.CharField(widget=forms.Select(choices=CHROMOSOMES),
                            required=True, max_length=3,
                            label='Chromosome')
    pos = forms.IntegerField(required=True, label='Position (1-based)',
                             min_value=1)


class AlleleForm(PointForm):
    ref = forms.CharField(label='Reference',
                          widget=forms.Select(choices=NUCLEOTIDES),
                          max_length=1, required=True)
    alt = forms.CharField(label='Substitution',
                          widget=forms.Select(choices=NUCLEOTIDES),
                          max_length=1, required=True)


class BulkForm(AssemblyForm):
    file = forms.FileField(required=True, label='Input file')
