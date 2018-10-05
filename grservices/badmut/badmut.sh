#! /usr/bin/env bash

set -o nounset
set -o pipefail

root=$(dirname "$0")
snpsift="java -jar ${SNPEFF_ROOT}/SnpSift.jar"
database=$([ "$1" == '19' ] && echo "${root}/hg19.vcf.gz" || echo "${root}/hg38.vcf.gz")
input="$2"
output="$3"


# account for header lines while truncating the input
takelines=$((500000 + $(gzip -cdf ${input} | head -n 500 | grep -c "^#")))
gzip -cdf ${input} | head -n ${takelines} | ${snpsift} annotate -tabix ${database} \
    | grep -v "^##SnpSift" | bgzip -c > ${output} || if [[ $? -eq 141 ]]; then true; else exit $?; fi
