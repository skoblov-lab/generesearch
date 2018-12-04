import os
import subprocess as sp
import tempfile
from collections import OrderedDict
from contextlib import contextmanager
from typing import Mapping, Optional, Any

import pandas as pd
from django.conf import settings
from vcf import Reader

from services import optional
from services.forms import VcfAnnotationForm, AlleleAnnotationForm, \
    PointAnnotationForm, ASSEMBLY, CHROM, POS, REF, ALT, FILE, FORM_TYPE


def silentrm(path):
    try:
        os.remove(path)
    except OSError:
        pass


@contextmanager
def cleanup(path):
    try:
        yield path
    finally:
        silentrm(path)


def genvcf(suffix, chrom, pos, ref, alt) -> str:
    # TODO purify
    with tempfile.NamedTemporaryFile(mode='w', dir=settings.MEDIA_ROOT,
                                     delete=False, suffix=suffix) as out:
        vcf = settings.VCF_TEMPLATE.format(chrom=chrom, pos=pos, ref=(ref or '.'), alt=(alt or '.'))
        print(vcf, file=out, end=('' if vcf.endswith('\n') else '\n'))
        return out.name


def convert_point_vcf(rec: "a PyVCF record") -> Optional[pd.DataFrame]:
    def field_converter(val):
        return list(filter(
            bool, [val if isinstance(val, str) else ','.join(map(str, val))]
        ))
    chrom, pos, ref, alt, info = rec.CHROM, rec.POS, rec.REF, rec.ALT, rec.INFO
    info_converted = {key: field_converter(value) for key, value in info.items()}
    if not (info_converted and any(info_converted.values())):
        return None
    items = [(CHROM, [chrom]), (POS, [pos]), (REF, [ref or '']),
             (ALT, [','.join([sub.sequence for sub in filter(bool, alt)])]),
             *info_converted.items()]
    return pd.DataFrame.from_dict(OrderedDict(items))


# TODO replace the `badmut`/`mirna` copy-paste job with a generic solution

@optional.fallible(Exception)
def badmut(fields: Mapping[str, Optional[Any]]) -> str:
    form_type = fields.get(FORM_TYPE) or ''
    if form_type == AlleleAnnotationForm.__name__:
        # create a temporary input file
        inpath = genvcf('.point.vcf', fields[CHROM], fields[POS], fields[REF],
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
    outpath = f'{inpath.split(".", 1)[0]}.badmut.vcf.gz'
    assembly = fields[ASSEMBLY]
    with cleanup(inpath):
        command = [settings.BADMUT_EXEC, assembly, inpath, outpath]
        try:
            sp.run(command, check=True, stderr=sp.PIPE)
        except (sp.CalledProcessError, ValueError):
            raise ValueError('Invalid file format')
        # convert point VCF output into a TSV file
        if form_type == AlleleAnnotationForm.__name__:
            with cleanup(outpath):
                record = convert_point_vcf(
                    next(Reader(filename=outpath, compressed=True))
                )
                result = f'{".".join(outpath.split(".")[:-2])}.tsv'
                # if no annotations were added, write an empty file
                if record is not None:
                    record.to_csv(result, sep='\t', index=False)
                else:
                    with open(result, 'w') as out:
                        print('#No annotations found', file=out)
                return result
        return outpath


@optional.fallible(Exception)
def mirna(fields: Mapping[str, Optional[Any]]) -> str:
    form_type = fields.get(FORM_TYPE) or ''
    if form_type == PointAnnotationForm.__name__:
        # create a temporary input file
        inpath = genvcf('.point.vcf', fields[CHROM], fields[POS], '.', '.')
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
    outpath = f'{inpath.split(".", 1)[0]}.mirna.vcf.gz'
    assembly = fields[ASSEMBLY]
    with cleanup(inpath):
        command = [settings.MIRNA_EXEC, assembly, inpath, outpath]
        try:
            sp.run(command, check=True, stderr=sp.PIPE)
        except (sp.CalledProcessError, ValueError):
            raise ValueError('Invalid file format')
        # convert point VCF output into a TSV file
        if form_type == PointAnnotationForm.__name__:
            with cleanup(outpath):
                record = convert_point_vcf(
                    next(Reader(filename=outpath, compressed=True))
                )
                result = f'{".".join(outpath.split(".")[:-2])}.tsv'
                # if no annotations were added, write an empty file
                if record is not None:
                    record.to_csv(result, sep='\t', index=False)
                else:
                    with open(result, 'w') as out:
                        print('#No annotations found', file=out)
                return result
        return outpath


# Can't pass
ACTIONS: Mapping[str, optional.ServiceAction] = {
    badmut.__name__: badmut,
    mirna.__name__: mirna
}


if __name__ == '__main__':
    raise RuntimeError
