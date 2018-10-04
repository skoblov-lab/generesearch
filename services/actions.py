import gzip
import os
import subprocess as sp
import tempfile
import logging
from collections import OrderedDict
from typing import Mapping, Optional, Any

import pandas as pd
from django.conf import settings
from vcf import Reader

from services import optional
from services.forms import VcfAnnotationForm, AlleleAnnotationForm, \
    PointAnnotationForm, ASSEMBLY, CHROM, POS, REF, ALT, FILE, FORM_TYPE


def genvcf(suffix, chrom, pos, ref, alt) -> str:
    # TODO purify
    with tempfile.NamedTemporaryFile(mode='w', dir=settings.MEDIA_ROOT,
                                     delete=False, suffix=suffix) as out:
        vcf = settings.VCF_TEMPLATE.format(chrom=chrom, pos=pos, ref=ref, alt=alt)
        print(vcf, file=out, end=('' if vcf.endswith('\n') else '\n'))
        return out.name


def convert_point_vcf(rec: "a PyVCF record") -> pd.DataFrame:
    def field_converter(value):
        return [value if isinstance(value, str) else ','.join(map(str, value))]
    chrom, pos, ref, alt, info = rec.CHROM, rec.POS, rec.REF, rec.ALT, rec.INFO
    info_coverted = {key: field_converter(value) for key, value in info.items()}
    items = [(CHROM, [chrom]), (POS, [pos]), (REF, [ref or '']),
             (ALT, [','.join([sub.sequence for sub in filter(bool, alt)])]),
             *info_coverted.items()]
    return pd.DataFrame.from_dict(OrderedDict(items))


# TODO replace the `badmut`/`mirna` copy-paste job with a generic solution

@optional.fallible(Exception)
def badmut(fields: Mapping[str, Optional[Any]]) -> str:
    form_type = fields.get(FORM_TYPE) or ''
    if form_type == AlleleAnnotationForm.__name__:
        # create a temporary input file
        inpath = genvcf('.upload.vcf', fields[CHROM], fields[POS], fields[REF],
                        fields[ALT])
    elif form_type == VcfAnnotationForm.__name__:
        # make sure the upload is ok
        upload = fields[FILE]
        if not upload:
            raise ValueError('Upload error')
        inpath = os.path.join(settings.MEDIA_ROOT, upload)
    # make sure the functions didn't receive an unexpected form
    else:
        raise ValueError('Invalid form')
    # run the tool
    assembly = fields[ASSEMBLY]
    outpath = f'{inpath.split(".", 1)[0]}.badmut.vcf.gz'
    command = [settings.BADMUT_EXEC, assembly, inpath, outpath]
    try:
        sp.run(command, check=True, stderr=sp.PIPE)
    except (sp.CalledProcessError, ValueError) as err:
        logging.exception(err)
        raise ValueError('Invalid file format')
    # convert point VCF output into a TSV file
    if form_type == AlleleAnnotationForm.__name__:
        record = convert_point_vcf(next(Reader(filename=outpath, compressed=True)))
        result = f'{".".join(outpath.split(".")[:-2])}.tsv'
        record.to_csv(result, sep='\t', index=False)
        # remove the VCF output
        os.remove(outpath)
    else:
        result = outpath
    return result


@optional.fallible(Exception)
def mirna(fields: Mapping[str, Optional[Any]]) -> str:
    form_type = fields.get(FORM_TYPE) or ''
    if form_type == PointAnnotationForm.__name__:
        # create a temporary input file
        inpath = genvcf('.upload.vcf', fields[CHROM], fields[POS], '.', '.')
    elif form_type == VcfAnnotationForm.__name__:
        # make sure the upload is ok
        upload = fields[FILE]
        if not upload:
            raise ValueError('Upload error')
        inpath = os.path.join(settings.MEDIA_ROOT, upload)
    # make sure the functions didn't receive an unexpected form
    else:
        raise ValueError('Invalid form')
    # run the tool
    assembly = fields[ASSEMBLY]
    outpath = f'{inpath.split(".", 1)[0]}.mirna.vcf.gz'
    command = [settings.MIRNA_EXEC, assembly, inpath, outpath]
    try:
        sp.run(command, check=True, stderr=sp.PIPE)
    except (sp.CalledProcessError, ValueError):
        raise ValueError('Invalid file format')
    # convert point VCF output into a TSV file
    if form_type == PointAnnotationForm.__name__:
        record = convert_point_vcf(next(Reader(filename=outpath, compressed=True)))
        result = f'{".".join(outpath.split(".")[:-2])}.tsv'
        record.to_csv(result, sep='\t', index=False)
        # remove the VCF output
        os.remove(outpath)
    else:
        result = outpath
    return result


# Can't pass
ACTIONS: Mapping[str, optional.ServiceAction] = {
    badmut.__name__: badmut,
    mirna.__name__: mirna
}

# def bmsubmit_vcf(form: VcfAnnotationForm) -> str:
#     """
#     Submit a bulk BadMut query
#     :param form: a bound form
#     :return:
#     """
#     upload = form.cleaned_data['file']
#     assembly = form.cleaned_data['assembly']
#     filepath = os.path.join(settings.MEDIA_ROOT, upload.name)
#     return tasks.vcfservice.delay(
#         tasks.BADMUT, assembly, filepath, upload.error).task_id
#
#
# def bmsubmit_allele(form: AlleleAnnotationForm) -> str:
#     """
#     Submit a point BadMut query
#     :param form: a bound form
#     :return:
#     """
#     data = form.cleaned_data
#     assembly, chrom, pos, ref, alt = [
#         data[key] for key in ('assembly', 'chrom', 'pos', 'ref', 'alt')
#     ]
#     with tempfile.NamedTemporaryFile(mode='w', dir=settings.MEDIA_ROOT,
#                                      delete=False, suffix='.upload.vcf') as out:
#         print(VCF_TEMPLATE.format(chrom, pos, ref, alt), file=out)
#         filepath = out.name
#     return tasks.vcfservice.delay(
#         tasks.BADMUT, assembly, filepath, None).task_id
#
#
# def mirnasubmit(form: PointAnnotationForm) -> str:
#     """
#     Submit a bulk miRNA query
#     :param form: a bound form
#     :return:
#     """
#     upload = form.cleaned_data['file']
#     assembly = form.cleaned_data['assembly']
#     filepath = os.path.join(settings.MEDIA_ROOT, upload.name)
#     return tasks.vcfservice.delay(
#         tasks.MIRNA, assembly, filepath, upload.error).task_id


if __name__ == '__main__':
    raise RuntimeError
