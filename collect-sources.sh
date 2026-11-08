#!/bin/bash
# Collects the complete corresponding source of libmpv-2.dll (LGPL obligation):
# - every package mpv depends on, as downloaded (before any build step),
# - the build recipes (mpv-winbuild-cmake after lgpl-config.py, with its patches),
# - a manifest with the exact git commit of each package,
# - the license files of each package (for the notices shipped with the DLL).
# Run after cmake configure, before building (downloads what is missing itself).
# Usage: collect-sources.sh <mpv-winbuild-cmake dir> <build dir> <output dir>
set -euo pipefail

cmake_dir=$(realpath "$1")
build_dir=$(realpath "$2")
out=$(realpath -m "$3")
mkdir -p "$out/licenses"
manifest="$out/MANIFEST.txt"
tarball="$out/sources.tar"

# Packages in the dependency graph of the mpv target.
mapfile -t packages < <(ninja -C "$build_dir" -t graph mpv \
    | grep -oE 'packages/[A-Za-z0-9_.+-]+-prefix/' \
    | sed -E 's#^packages/(.*)-prefix/$#\1#' | sort -u)
[ "${#packages[@]}" -gt 0 ] || { echo "No package found in the mpv graph" >&2; exit 1; }

# GPL packages of mpv-winbuild-cmake: none of them may be linked into the DLL.
gpl_packages="x264 x265 xvidcore davs2 rubberband lzo libdvdcss libdvdnav libdvdread libzvbi readline termcap"
for pkg in "${packages[@]}"; do
    if [[ " $gpl_packages " == *" $pkg "* ]]; then
        echo "GPL package '$pkg' is in the mpv dependency graph" >&2
        exit 1
    fi
done

# The `download` target of mpv-winbuild-cmake skips some packages mpv still needs (libsixel...): download exactly
# the packages of the mpv graph.
ninja -C "$build_dir" "${packages[@]/%/-download}"

{
    echo "libmpv-2.dll - corresponding source"
    echo "Built with mpv-winbuild-cmake $(git -C "$cmake_dir" rev-parse HEAD) (recipes in build-recipes/, modified by lgpl-config.py)"
    echo
    printf '%-24s %s\n' "package" "origin"
} > "$manifest"

missing=0
rm -f "$tarball"
for pkg in "${packages[@]}"; do
    src=""
    for candidate in "$cmake_dir/src_packages/$pkg" "$build_dir/packages/$pkg-prefix/src/$pkg"; do
        if [ -d "$candidate" ] && [ -n "$(ls -A "$candidate")" ]; then src="$candidate"; break; fi
    done
    if [ -z "$src" ]; then
        printf '%-24s MISSING\n' "$pkg" >> "$manifest"
        missing=1
        continue
    fi
    if git -C "$src" rev-parse --show-toplevel 2>/dev/null | grep -qx "$src"; then
        origin="$(git -C "$src" remote get-url origin 2>/dev/null || echo '?') @ $(git -C "$src" rev-parse HEAD)"
    else
        origin="release archive"
    fi
    printf '%-24s %s\n' "$pkg" "$origin" >> "$manifest"
    tar -rf "$tarball" --exclude-vcs -C "$(dirname "$src")" --transform "s#^$(basename "$src")#packages/$pkg#" "$(basename "$src")"

    mkdir -p "$out/licenses/$pkg"
    find "$src" -maxdepth 1 -type f \( -iname 'COPYING*' -o -iname 'LICENSE*' -o -iname 'LICENCE*' -o -iname 'COPYRIGHT*' -o -iname 'NOTICE*' \) \
        -exec cp {} "$out/licenses/$pkg/" \;
    [ -n "$(ls -A "$out/licenses/$pkg")" ] || echo "no license file at the root of $pkg" >> "$out/licenses/MISSING.txt"
done

# Build recipes, as modified by lgpl-config.py.
tar -rf "$tarball" --exclude-vcs -C "$(dirname "$cmake_dir")" \
    --exclude="$(basename "$cmake_dir")/src_packages" --exclude="$(basename "$cmake_dir")/build*" \
    --exclude="$(basename "$cmake_dir")/install_rustup" --exclude="$(basename "$cmake_dir")/clang_root" \
    --exclude="$(basename "$cmake_dir")/release" \
    --transform "s#^$(basename "$cmake_dir")#build-recipes#" "$(basename "$cmake_dir")"
tar -rf "$tarball" -C "$out" --transform 's#^#build-recipes/#' MANIFEST.txt

if [ "$missing" -ne 0 ]; then
    echo "Some sources are missing, see $manifest" >&2
    grep MISSING "$manifest" >&2
    exit 1
fi
echo "${#packages[@]} packages collected."
