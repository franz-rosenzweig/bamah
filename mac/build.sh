#!/bin/zsh
# Builds Bamah.app with the Command Line Tools alone, no Xcode project:
#   ./build.sh && open build/Bamah.app
# BAMAH_DEFAULT_SERVER (or local.env beside this script, which git leaves out) is the address
# offered the first time. BAMAH_SIGN names a signing identity; without one it's signed ad hoc,
# which is enough on the Mac that built it. BAMAH_SELFTEST=1 builds in SelfTest/ (selftest.sh).
set -euo pipefail
cd "${0:A:h}"

VERSION=0.1.0
BUILD=1
MACOS=13.0
[[ -z ${BAMAH_DEFAULT_SERVER:-} && -f local.env ]] && source ./local.env
OUT=${BAMAH_OUT:-build}
APP=$OUT/Bamah.app

command -v swiftc >/dev/null || { echo "no swiftc: run xcode-select --install" >&2; exit 1; }
rm -rf $APP && mkdir -p $APP/Contents/MacOS $APP/Contents/Resources

SRC=(Bamah/*.swift)
FLAGS=()
if [[ -n ${BAMAH_SELFTEST:-} ]]; then SRC+=(SelfTest/SelfTest.swift); FLAGS+=(-D SELFTEST); fi

# Apple silicon and Intel both
for arch in arm64 x86_64; do
    swiftc -O -wmo -sdk "$(xcrun --show-sdk-path)" -target $arch-apple-macos$MACOS -swift-version 5 \
        -parse-as-library -module-name Bamah -enable-upcoming-feature ConciseMagicFile $FLAGS $SRC -o $OUT/Bamah-$arch
done
lipo -create $OUT/Bamah-arm64 $OUT/Bamah-x86_64 -output $APP/Contents/MacOS/Bamah
rm -f $OUT/Bamah-arm64 $OUT/Bamah-x86_64

sed -e "s/@VERSION@/$VERSION/" -e "s/@BUILD@/$BUILD/" -e "s/@BUNDLE_ID@/${BAMAH_BUNDLE_ID:-xyz.tiresia.bamah}/" \
    -e "s#@SERVER@#${BAMAH_DEFAULT_SERVER:-}#" Info.plist > $APP/Contents/Info.plist
plutil -lint -s $APP/Contents/Info.plist

# The icon: icon-1024.png is the web app's, drawn on the 824-of-1024 grid macOS icons use
SET=$OUT/AppIcon.iconset && rm -rf $SET && mkdir -p $SET
for s in 16 32 128 256 512; do
    sips -z $s $s icon-1024.png --out $SET/icon_${s}x${s}.png >/dev/null
    sips -z $((s * 2)) $((s * 2)) icon-1024.png --out $SET/icon_${s}x${s}@2x.png >/dev/null
done
iconutil -c icns $SET -o $APP/Contents/Resources/AppIcon.icns
rm -rf $SET

codesign --force --options runtime --entitlements Bamah.entitlements --sign "${BAMAH_SIGN:--}" $APP
# nothing of the computer that built it: no home folder's path in the app
! grep -r -l -a "/Users/" $APP >/dev/null || { echo "a home folder's path is in the app" >&2; exit 1; }
echo "built $APP ($VERSION)"
