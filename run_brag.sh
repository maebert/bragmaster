#!/bin/bash
tmpfile=$(mktemp /tmp/brag.XXXXXX)
brag.py template > $tmpfile
open -b pro.writer.mac -Wn $tmpfile
brag.py update -w < $tmpfile
rm $tmpfile
