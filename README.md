# libmpv-build

LGPL build of `libmpv-2.dll` for Windows x86_64, used by FilePeak's video player.
No GPL and no non-free code: mpv is built with `-Dgpl=false` (LGPL 2.1+), FFmpeg without
`--enable-gpl` / `--enable-nonfree` (LGPL 3+).

## How it works

The build runs on GitHub Actions (`.github/workflows/build.yml`, started by hand) with the
recipes of [shinchiro/mpv-winbuild-cmake](https://github.com/shinchiro/mpv-winbuild-cmake),
pinned in `versions.env`:

1. `lgpl-config.py` edits the recipes: GPL-only libraries removed (x264, x265, davs2,
   rubberband, libzvbi, AviSynth, dvdnav/dvdread), features the player does not need removed
   (Lua, JavaScript, libcurl, libbluray, VapourSynth, OpenAL, subrandr), libmpv only.
   No Vulkan: the DLL does not import `vulkan-1.dll` and renders through Direct3D 11.
   Each edit is an exact match: if upstream changes, the script fails instead of guessing.
2. `collect-sources.sh` downloads every package mpv depends on and archives them before any
   build step, with the recipes and the license files, and writes `MANIFEST.txt` with the
   exact commit of each package.
3. libmpv is built, then `check-lgpl.sh` reads the configuration FFmpeg and mpv actually
   used (their configure output) and the strings of the DLL, and fails on any GPL or
   non-free setting.
4. With a `release_tag`, the DLL, the complete source and the licenses are published as a
   GitHub release. Releases are never deleted: they are the source offer of the DLLs
   distributed with FilePeak.

The build job uploads its result as the `build-output` artifact. To rerun only the LGPL check,
the packaging and the release (after changing `check-lgpl.sh` or `NOTICE.md`, or to publish an
already built DLL), start the workflow with `reuse_run` set to the ID of that run (the number at
the end of its URL): no recompilation.

## Release assets

| File | Content |
| --- | --- |
| `libmpv-lgpl-x86_64.zip` | `libmpv-2.dll`, `MANIFEST.txt`, `LGPL-CHECK.txt` |
| `libmpv-lgpl-x86_64-sources.tar.xz` | Complete corresponding source |
| `libmpv-lgpl-x86_64-licenses.zip` | License files of every component, `NOTICE.md` |
| `SHA256SUMS.txt` | Checksums |

## Rebuilding

Fork the repository and run the workflow, or follow `build.yml` on an Arch Linux machine.
The resulting `libmpv-2.dll` can replace the one shipped with FilePeak.
