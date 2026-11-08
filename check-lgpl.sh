#!/bin/bash
# Fails if the built libmpv-2.dll contains GPL or non-free code.
# Reads the configuration that FFmpeg and mpv actually used (config.h of each
# build directory) and the strings embedded in the DLL, not the recipes.
# Usage: check-lgpl.sh path/to/libmpv-2.dll path/to/build64
set -euo pipefail

dll="$1"
builddir="$2"
fail() { echo "LGPL CHECK FAILED: $*" >&2; exit 1; }

# FFmpeg: config.h written by configure (--enable-gpl / --enable-version3 / --enable-nonfree).
ffconfig=$(grep -rl --include=config.h '#define FFMPEG_LICENSE' "$builddir/packages" | head -n1 || true)
[ -n "$ffconfig" ] || fail "FFmpeg config.h not found in $builddir/packages"
license=$(sed -n 's/^#define FFMPEG_LICENSE "\(.*\)"$/\1/p' "$ffconfig")
[ "$license" = "LGPL version 3 or later" ] || fail "FFmpeg license is '$license'"
ffconf=$(sed -n 's/^#define FFMPEG_CONFIGURATION "\(.*\)"$/\1/p' "$ffconfig")
for flag in --enable-gpl --enable-nonfree; do
    if grep -q -- "$flag" <<< "$ffconf"; then fail "FFmpeg configured with $flag"; fi
done

# mpv: config.h written by meson.
mpvconfig=$(grep -rl --include=config.h '#define FULLCONFIG' "$builddir/packages" | head -n1 || true)
[ -n "$mpvconfig" ] || fail "mpv config.h not found in $builddir/packages"
if grep -qE '^#define HAVE_GPL [^0]' "$mpvconfig"; then fail "mpv built with HAVE_GPL"; fi
features=$(sed -n 's/^#define FULLCONFIG "\(.*\)"$/\1/p' "$mpvconfig")
if grep -qw 'gpl' <<< "$features"; then fail "mpv feature list contains 'gpl'"; fi

# The DLL itself must carry the same mpv feature list (proves config.h belongs to this DLL).
strings -a -n 6 "$dll" | grep -qxF -- "$features" || fail "mpv feature list of config.h not found in $dll"

echo "FFmpeg license: $license"
echo "FFmpeg configuration: $ffconf"
echo "mpv features: $features"
echo "Imported DLLs:"
"${OBJDUMP:-objdump}" -p "$dll" | grep 'DLL Name' | sed 's/^\s*/  /'
echo "LGPL check passed."
