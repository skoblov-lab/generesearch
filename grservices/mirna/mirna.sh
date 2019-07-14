#! /usr/bin/env bash

set -o nounset
set -o pipefail

root=$(dirname "$0")
version="$1"
input="$2"
output="$3"

# select contig naming version (with or without prefix `chr`)
if grep -v '^#' "${input}" | head -n 1 | grep -q '^chr'; then
    database="${root}/db/hg${version}-chrom.annotation.tsv.gz"
    contigs="${root}/db/contigs-chrom.txt"
else
    database="${root}/db/hg${version}-nochrom.annotation.tsv.gz"
    contigs="${root}/db/contigs-nochrom.txt"
fi

columns="$(cat ${root}/db/annotation.colnames)"
infoheader="${root}/db/annotation.hdr"
add_contigs="${root}/add_contigs.py"

# account for header lines while truncating the input
takelines=$((500000 + $(gzip -cdf "${input}" | head -n 500 | grep -c "^#")))
# annotate
gzip -cdf "${input}" | head -n "${takelines}" \
    | python "${add_contigs}" -c "${contigs}" \
    | bcftools annotate -a "${database}" -c "${columns}" -h "${infoheader}" \
    | bgzip -c > "${output}" || if [[ $? -eq 141 ]]; then true; else exit $?; fi
