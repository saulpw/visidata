#!/bin/bash

for fn in tests/*.vd ; do
    if [ "${fn%-notest.vd}-notest" != "${fn%.vd}" ]
    then
        fna=${fn##tests/}
        tsvfn=tests/golden/${fna%.vd}.tsv
        git show HEAD^:$tsvfn | bin/vd --diff $tsvfn
    fi
done
