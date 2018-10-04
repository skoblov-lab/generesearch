from django import forms
from itertools import chain


HG19 = '19'
HG38 = '38'
VCF = 'vcf'
TSV = 'tsv'
ASSEMBLIES = ((HG38,)*2, (HG19,)*2)
OUTPUT_FORMATS = ((VCF,) * 2, (TSV,) * 2)
NUCLEOTIDES = (
    ('A', 'A'),
    ('C', 'C'),
    ('G', 'G'),
    ('T', 'T')
)
CHROMOSOMES = tuple(
    (chrom, chrom) for chrom in map(str, chain(range(1, 23), 'MXY'))
)


class BaseAnnotationServiceForm(forms.Form):
    assembly = forms.CharField(widget=forms.Select(choices=ASSEMBLIES),
                               label='Human genome assembly version',
                               max_length=2, required=True)
    # output_format = forms.CharField(widget=forms.Select(choices=OUTPUT_FORMATS),
    #                                 label='Output format',
    #                                 max_length=3, required=True)
    # compress = forms.BooleanField(initial=True, label='Compress the output')


class PointAnnotationForm(BaseAnnotationServiceForm):
    chrom = forms.CharField(widget=forms.Select(choices=CHROMOSOMES),
                            required=True, max_length=3,
                            label='Chromosome')
    pos = forms.IntegerField(required=True, label='Position (1-based)',
                             min_value=1)


class AlleleAnnotationForm(PointAnnotationForm):
    ref = forms.CharField(label='Reference',
                          widget=forms.Select(choices=NUCLEOTIDES),
                          max_length=1, required=True)
    alt = forms.CharField(label='Substitution',
                          widget=forms.Select(choices=NUCLEOTIDES),
                          max_length=1, required=True)


class VcfAnnotationForm(BaseAnnotationServiceForm):
    file = forms.FileField(required=True, label='Input file')


if __name__ == '__main__':
    raise RuntimeError
