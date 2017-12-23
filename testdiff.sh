#!/bin/bash

for fn in `git diff --name-only -- *.tsv` ; do
    if [ "${fn%-notest.tsv}-notest" != "${fn%.tsv}" ]
    then
        git show HEAD^:$fn | bin/vd --diff $fn
    fi
done
