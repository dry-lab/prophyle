#! /usr/bin/env bash -f -e -o pipefail

prophyle=./prophyle/prophyle.py

$prophyle download bacteria
$prophyle index -k 5 ~/prophyle/test_bacteria.nw test_idx

