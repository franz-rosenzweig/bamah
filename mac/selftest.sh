#!/bin/zsh
# Tests the app from inside against a running Bamah (a demo is best: python tools/demo.py --serve):
#   ./selftest.sh http://127.0.0.1:8498 '#/scene/1'
# It builds a copy with SelfTest/ in it under another bundle id (so her settings stay as they are),
# opens the page, works the menus, and leaves log.txt and pictures in build/selftest/out.
set -euo pipefail
cd "${0:A:h}"
SERVER=${1:?the address of a Bamah to test against}
START=${2:-#/}
OUT=build/selftest
rm -rf $OUT/out && mkdir -p $OUT/out
BAMAH_OUT=$OUT BAMAH_BUNDLE_ID=xyz.tiresia.bamah.selftest BAMAH_SELFTEST=1 ./build.sh >/dev/null
open -W -n $OUT/Bamah.app --args -BamahServerOnce "$SERVER" -BamahStart "$START" -BamahSelfTest "$PWD/$OUT/out"
cat $OUT/out/log.txt
grep -q '^PASSED' $OUT/out/log.txt
