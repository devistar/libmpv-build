#!/bin/bash
# Fails if the built libmpv-2.dll contains GPL or non-free code.
# The recipes delete each package's build directory once installed (postremovebuild), so config.h is gone:
# reads what configure printed (stamp logs, kept) and checks it against the strings embedded in the DLL.
# Usage: check-lgpl.sh path/to/libmpv-2.dll path/to/build64
set -euo pipefail

dll="$1"
builddir="$2"
fail() { echo "LGPL CHECK FAILED: $*" >&2; exit 1; }

# Strings of the DLL in a file: piping into grep -q would kill strings with SIGPIPE (pipefail).
dllstrings=$(mktemp)
trap 'rm -f "$dllstrings"' EXIT
strings -a -n 6 "$dll" > "$dllstrings"

# FFmpeg: license printed by configure, and the license strings compiled into the DLL (avutil_license...).
fflog="$builddir/packages/ffmpeg-prefix/src/ffmpeg-stamp/ffmpeg-configure-out.log"
[ -f "$fflog" ] || fail "$fflog not found"
license=$(sed -n 's/^License: //p' "$fflog")
[ "$license" = "LGPL version 3 or later" ] || fail "FFmpeg configure reports license '$license'"
grep -qxF "LGPL version 3 or later" "$dllstrings" || fail "FFmpeg LGPL license string not found in $dll"
for other in "GPL version 2 or later" "GPL version 3 or later" "nonfree and unredistributable"; do
    if grep -qxF "$other" "$dllstrings"; then fail "$dll contains FFmpeg license '$other'"; fi
done
if grep -qE -- '(^| )--enable-(gpl|nonfree)( |$)' "$dllstrings"; then fail "FFmpeg configured with --enable-gpl or --enable-nonfree"; fi
ffconf=$(grep -m1 -E -- '(^| )--enable-' "$dllstrings" || true)

# mpv: feature list printed by meson, which is also FULLCONFIG compiled into the DLL.
mpvlog="$builddir/packages/mpv-prefix/src/mpv-stamp/mpv-configure-out.log"
[ -f "$mpvlog" ] || fail "$mpvlog not found"
features=$(sed -n 's/^Message: List of enabled features: //p' "$mpvlog")
[ -n "$features" ] || fail "mpv feature list not found in $mpvlog"
if grep -qw 'gpl' <<< "$features"; then fail "mpv feature list contains 'gpl'"; fi
grep -qxF -- "$features" "$dllstrings" || fail "mpv feature list of the configure log not found in $dll"

echo "FFmpeg license: $license"
echo "FFmpeg configuration: ${ffconf:-(not found in the DLL strings)}"
echo "mpv features: $features"
echo "Imported DLLs:"
"${OBJDUMP:-objdump}" -p "$dll" | grep 'DLL Name' | sed 's/^\s*/  /'
echo "LGPL check passed."
