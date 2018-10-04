from itertools import chain
from typing import Mapping, Optional, Any

from django import forms

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
ASSEMBLY = 'assembly'
CHROM = 'chrom'
POS = 'pos'
REF = 'ref'
ALT = 'alt'
FILE = 'file'
FORM_TYPE = 'form_type'


class BaseAnnotationServiceForm(forms.Form):
    assembly = forms.CharField(widget=forms.Select(choices=ASSEMBLIES),
                               label='Human genome assembly version',
                               max_length=2, required=True)
    # output_format = forms.CharField(widget=forms.Select(choices=OUTPUT_FORMATS),
    #                                 label='Output format',
    #                                 max_length=3, required=True)
    # compress = forms.BooleanField(initial=True, label='Compress the output')

    def serialise_fields(self) -> Mapping[str, Optional[Any]]:
        """
        Making forms serialisable for Celery by extracting relevant fields and
        packing them into a dictionary
        :return:
        """
        return {FORM_TYPE: type(self).__name__,
                ASSEMBLY: self.cleaned_data[ASSEMBLY]}


class PointAnnotationForm(BaseAnnotationServiceForm):
    chrom = forms.CharField(widget=forms.Select(choices=CHROMOSOMES),
                            required=True, max_length=3,
                            label='Chromosome')
    pos = forms.IntegerField(required=True, label='Position (1-based)',
                             min_value=1)

    def serialise_fields(self):
        data = self.cleaned_data
        return {CHROM: data[CHROM], POS: data[POS], **super().serialise_fields()}


class AlleleAnnotationForm(PointAnnotationForm):
    ref = forms.CharField(label='Reference',
                          widget=forms.Select(choices=NUCLEOTIDES),
                          max_length=1, required=True)
    alt = forms.CharField(label='Substitution',
                          widget=forms.Select(choices=NUCLEOTIDES),
                          max_length=1, required=True)

    def serialise_fields(self):
        data = self.cleaned_data
        return {REF: data[REF], ALT: data[ALT], **super().serialise_fields()}


class VcfAnnotationForm(BaseAnnotationServiceForm):
    file = forms.FileField(required=True, label='Input file')

    def serialise_fields(self):
        data = self.cleaned_data
        upload = data[FILE]
        return {FILE: (None if upload.error else upload.name),
                **super().serialise_fields()}


if __name__ == '__main__':
    raise RuntimeError
